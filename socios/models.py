from django.db import models
from django.conf import settings

class Socio(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil_socio', null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=15, unique=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_alta = models.DateField(auto_now_add=True)

    @classmethod
    def para_usuario(cls, usuario):
        """Perfil de socio del usuario; si no tiene, lo crea con un DNI que no esté repetido."""
        perfil = cls.objects.filter(usuario=usuario).first()
        if perfil:
            return perfil
        largo = cls._meta.get_field('dni').max_length
        dni = (usuario.dni or usuario.username)[:largo]
        existente = cls.objects.filter(dni=dni).first()
        if existente and existente.usuario is None:
            existente.usuario = usuario
            existente.save(update_fields=['usuario'])
            return existente
        if existente:
            dni = f'ID-{usuario.pk}'
        return cls.objects.create(
            usuario=usuario,
            dni=dni,
            nombre=usuario.first_name[:100],
            apellido=usuario.last_name[:100],
            email=usuario.email,
        )

    def __str__(self):
        return f"{self.apellido}, {self.nombre} (DNI: {self.dni})"
