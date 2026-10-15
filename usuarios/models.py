from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings

# 1. MODELO PRINCIPAL DE USUARIOS DE GYMTRACK
class Usuario(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('recepcion', 'Recepción / Empleado'),
        ('entrenador', 'Entrenador'),
        ('socio', 'Socio'),
    )
    rol = models.CharField(max_length=20, choices=ROLES, default='socio')
    dni = models.CharField(max_length=20, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    estado_cuenta = models.CharField(max_length=10, default='VERDE')  # VERDE o ROJO

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"


# 2. MODELO DE FICHAJE DE JORNADA LABORAL DE EMPLEADOS
class AsistenciaEmpleado(models.Model):
    empleado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'rol__in': ['recepcion', 'entrenador', 'empleado']}
    )
    hora_entrada = models.DateTimeField(default=timezone.now)
    hora_salida = models.DateTimeField(null=True, blank=True)

    @property
    def horas_trabajadas(self):
        if self.hora_salida:
            diferencia = self.hora_salida - self.hora_entrada
            horas = diferencia.total_seconds() / 3600
            return f"{horas:.2f} hs"
        return "En curso"

    def __str__(self):
        return f"{self.empleado.username} - {self.hora_entrada.strftime('%d/%m/%Y %H:%M')}"