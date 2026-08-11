from django.db import models
from socios.models import Socio

class Ejercicio(models.Model):
    nombre = models.CharField(max_length=100) # Ej: Press de Banca
    grupo_muscular = models.CharField(max_length=50) # Ej: Pecho

    def __str__(self):
        return self.nombre

class Rutina(models.Model):
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE, related_name='rutinas')
    nombre = models.CharField(max_length=100) # Ej: Rutina Hipertrofia A
    fecha_creacion = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.socio}"