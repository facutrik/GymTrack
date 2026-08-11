from django.db import models
from socios.models import Socio

class Plan(models.Model):
    nombre = models.CharField(max_length=50) # Ej: "Musculación Pase Libre"
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_dias = models.IntegerField(default=30) # Ej: 30 días

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"

class MembresiaSocio(models.Model):
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE, related_name='membresias')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.socio} - {self.plan.nombre}"