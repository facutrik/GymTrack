from django.db import models
from django.conf import settings

class Actividad(models.Model):
    nombre = models.CharField(max_length=100) # Ej: Spinning, Crossfit
    descripcion = models.TextField(blank=True)
    cupo_maximo = models.IntegerField(default=20)

    def __str__(self):
        return self.nombre

class Clase(models.Model):
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    entrenador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    dia_semana = models.CharField(max_length=15) # Ej: "Lunes y Miércoles"
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.actividad.nombre} ({self.dia_semana} {self.hora_inicio})"