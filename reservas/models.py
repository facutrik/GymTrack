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

    def __str__(self):
        return f"Reserva {self.socio} - {self.clase} ({self.fecha_reserva})"