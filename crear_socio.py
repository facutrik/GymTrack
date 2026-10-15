import os
import django

# Configuramos el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymtrack.settings')
django.setup()

from usuarios.models import Usuario
from socios.models import Socio

# 1. Creamos o actualizamos el Usuario
usuario, created = Usuario.objects.get_or_create(username='40123456')
usuario.set_password('123')  # Cifra la clave obligatoriamente
usuario.first_name = 'Lucas'
usuario.last_name = 'Romero'
usuario.email = 'lucas.romero@gymtrack.com'
usuario.rol = 'socio'
usuario.is_active = True
usuario.estado_cuenta = 'VERDE'
if hasattr(usuario, 'dni'):
    usuario.dni = '40123456'
usuario.save()

# 2. Creamos o actualizamos el perfil de Socio
socio = Socio.objects.filter(usuario=usuario).first()
if not socio:
    socio = Socio(usuario=usuario)

# Asignamos campos solo si existen en el modelo Socio para evitar TypeErrors
if hasattr(socio, 'dni'):
    socio.dni = '40123456'
if hasattr(socio, 'estado_cuenta'):
    socio.estado_cuenta = 'VERDE'
socio.save()

print("\n" + "="*50)
print("✅ SOCIO CONFIGURADO EXITOSAMENTE")
print(f"Usuario / DNI: {usuario.username}")
print("Contraseña:    123")
print(f"Nombre:        {usuario.first_name} {usuario.last_name}")
print(f"Rol:           {usuario.rol}")
print(f"Activo:        {usuario.is_active}")
print("="*50 + "\n")