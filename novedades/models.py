from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class NovedadQuerySet(models.QuerySet):
    def visibles(self):
        """Las que se muestran en la campana: activas y sin vencer."""
        hoy = timezone.localdate()
        return self.filter(activa=True).filter(Q(visible_hasta__isnull=True) | Q(visible_hasta__gte=hoy))


class Novedad(models.Model):
    """Aviso que publica el personal y ven todos en la campana del nav."""
    CATEGORIAS = (
        ('general', 'General'),
        ('precios', 'Precios y cuotas'),
        ('horarios', 'Horarios'),
        ('clases', 'Clases y actividades'),
        ('mantenimiento', 'Mantenimiento'),
    )
    # (ícono de Font Awesome, color de Tailwind) para cada categoría
    ESTILOS = {
        'general': ('fa-bullhorn', 'blue'),
        'precios': ('fa-tags', 'amber'),
        'horarios': ('fa-clock', 'purple'),
        'clases': ('fa-dumbbell', 'emerald'),
        'mantenimiento': ('fa-screwdriver-wrench', 'rose'),
    }

    titulo = models.CharField(max_length=120)
    mensaje = models.TextField()
    categoria = models.CharField(max_length=15, choices=CATEGORIAS, default='general')
    visible_hasta = models.DateField(null=True, blank=True, help_text='Vacío = se muestra hasta que la archives.')
    activa = models.BooleanField(default=True)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    publicada = models.DateTimeField(auto_now_add=True)
    avisada_por_mail = models.BooleanField(default=False)

    objects = NovedadQuerySet.as_manager()

    class Meta:
        ordering = ['-publicada']
        verbose_name_plural = 'novedades'

    @property
    def icono(self):
        return self.ESTILOS.get(self.categoria, self.ESTILOS['general'])[0]

    @property
    def color(self):
        return self.ESTILOS.get(self.categoria, self.ESTILOS['general'])[1]

    @property
    def visible(self):
        return self.activa and (self.visible_hasta is None or self.visible_hasta >= timezone.localdate())

    def __str__(self):
        return self.titulo


class LecturaNovedades(models.Model):
    """Hasta cuándo vio las novedades cada usuario (para el número de "no leídas" de la campana)."""
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lectura_novedades')
    vistas_hasta = models.DateTimeField()

    def __str__(self):
        return f'{self.usuario} vio hasta {self.vistas_hasta:%d/%m/%Y %H:%M}'
