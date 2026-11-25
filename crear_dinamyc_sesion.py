import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymtrack.settings')
django.setup()

from usuarios.models import Usuario
from socios.models import Socio

# 1. Crear o actualizar usuario de prueba para Dinamyc Gym (Plan Start)
dni_prueba = '45999888'
usuario, _ = Usuario.objects.get_or_create(username=dni_prueba)
usuario.set_password('123')
usuario.first_name = 'Mateo'
usuario.last_name = 'Sosa'
usuario.email = 'mateo.dinamyc@gymtrack.com'
usuario.rol = 'socio'
usuario.is_active = True
if hasattr(usuario, 'estado_cuenta'):
    usuario.estado_cuenta = 'VERDE'
if hasattr(usuario, 'dni'):
    usuario.dni = dni_prueba
usuario.save()

# 2. Crear o actualizar su perfil en Socio evitando duplicados en dni
socio = Socio.objects.filter(usuario=usuario).first()
if not socio:
    socio = Socio(usuario=usuario)

if hasattr(socio, 'dni'):
    socio.dni = dni_prueba
if hasattr(socio, 'estado_cuenta'):
    socio.estado_cuenta = 'VERDE'
socio.save()

print("\n" + "=" * 50)
print("USUARIO DE PRUEBA DINAMYC GYM LISTO")
print(f"Usuario / DNI : {usuario.username}")
print("Contraseña    : 123")
print(f"Nombre        : {usuario.first_name} {usuario.last_name}")
print(f"Rol           : {usuario.rol}")
print("=" * 50 + "\n")