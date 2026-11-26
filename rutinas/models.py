from django.db import models
from django.conf import settings

class Rutina(models.Model):
    TIPO_CHOICES = (
        ('gimnasio', 'Rutina del Gimnasio'),
        ('personalizada', 'Personalizada por el Socio'),
    )
    socio = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rutinas')
    nombre = models.CharField(max_length=100, default='Mi Plan de Entrenamiento')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='personalizada')
    objetivo = models.CharField(max_length=150, default='Acondicionamiento General')
    creada_en = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.nombre} ({self.socio.username})"

class DiaEntrenamiento(models.Model):
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE, related_name='dias')
    numero_dia = models.IntegerField(default=1)  # 1 a 7
    nombre_dia = models.CharField(max_length=50)  # Lunes, Martes, etc.
    enfoque = models.CharField(max_length=100)     # Pecho / Tríceps, Piernas, Descanso, etc.
    class Meta:
        ordering = ['numero_dia']
    def __str__(self):
        return f"{self.nombre_dia} - {self.enfoque}"

class Ejercicio(models.Model):
    dia = models.ForeignKey(DiaEntrenamiento, on_delete=models.CASCADE, related_name='ejercicios')
    nombre = models.CharField(max_length=120)
    series = models.IntegerField(default=3)
    repeticiones = models.CharField(max_length=50, default='10-12')
    descanso = models.CharField(max_length=50, default='60s')
    def __str__(self):
        return f"{self.nombre} ({self.series}x{self.repeticiones})"

class RegistroUltimaSerie(models.Model):
    """Guarda únicamente el último peso y repeticiones de cada serie por usuario."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ultimas_series_rutina',
    )
    clave_serie = models.CharField(max_length=120)
    peso_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    repeticiones = models.PositiveIntegerField(null=True, blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('usuario', 'clave_serie')

    def __str__(self):
        return f"{self.usuario} - {self.clave_serie}: {self.peso_kg}kg x {self.repeticiones}"