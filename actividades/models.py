from django.db import models

class Actividad(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    requiere_reserva = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    def __str__(self):
        return self.nombre

class Clase(models.Model):
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='clases')
    nombre = models.CharField(max_length=100, blank=True, null=True)
    cupo_maximo = models.PositiveIntegerField(default=20)
    def __str__(self):
        return f"{self.actividad.nombre} - {self.nombre or 'General'}"
