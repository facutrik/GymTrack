from django.db import models
from socios.models import Socio
from actividades.models import Clase

class Reserva(models.Model):
    ESTADOS = (
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    )
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE)
    fecha_reserva = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADOS, default='confirmada')

    @classmethod
    def clase_de(cls, actividad):
        """La clase que define el cupo de la actividad (None si todavía no tiene)."""
        return Clase.objects.filter(actividad=actividad).order_by('id').first()

    @classmethod
    def cupo_de(cls, actividad):
        clase = cls.clase_de(actividad)
        return clase.cupo_maximo if clase else Clase._meta.get_field('cupo_maximo').default

    @classmethod
    def anotados_en(cls, actividad):
        return (
            cls.objects.filter(clase__actividad=actividad, estado='confirmada')
            .values('socio').distinct().count()
        )

    def __str__(self):
        return f"Reserva {self.socio} - {self.clase} ({self.fecha_reserva})"
