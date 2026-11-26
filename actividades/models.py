import re

from django.db import models

PATRON_PROFESOR = re.compile(r'\(\s*Prof(?:\.|esora?)?\s*([^)]+)\)', re.IGNORECASE)
PATRON_HORA = re.compile(r'^(\D*?)\s*(\d.*)$')

class Actividad(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    requiere_reserva = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    @property
    def sin_turno(self):
        """La sala de musculación es de acceso libre: no se reserva ni tiene cupo."""
        return 'musculaci' in self.nombre.lower()

    @property
    def profesor(self):
        """Profesor indicado en la descripción como "(Prof. Nombre Apellido)"."""
        hallado = PATRON_PROFESOR.search(self.descripcion or '')
        return hallado.group(1).strip() if hallado else ''

    @property
    def horarios(self):
        """Pares día/hora leídos de la descripción, por ejemplo "Lun 9-11hs, Mié 11-13hs"."""
        texto = PATRON_PROFESOR.sub('', self.descripcion or '').strip(' .')
        if not texto:
            return []
        partes = [p.strip() for p in texto.split(',')]
        if not all(any(c.isdigit() for c in p) for p in partes):
            partes = [texto]  # las comas separan días que comparten horario
        horarios = []
        for parte in partes:
            hallado = PATRON_HORA.match(parte)
            dias, hora = hallado.groups() if hallado else (parte, '')
            horarios.append({'dias': dias.strip() or 'Horario', 'hora': hora.strip()})
        return horarios

    def __str__(self):
        return self.nombre

class Clase(models.Model):
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='clases')
    nombre = models.CharField(max_length=100, blank=True, null=True)
    cupo_maximo = models.PositiveIntegerField(default=20)
    def __str__(self):
        return f"{self.actividad.nombre} - {self.nombre or 'General'}"
