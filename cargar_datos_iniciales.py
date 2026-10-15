import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymtrack.settings')
django.setup()

from actividades.models import Actividad
from membresias.models import Plan
from usuarios.models import Usuario

print("Iniciando carga de profesores, actividades y membresías...")

# ==========================================================
# 1. Asegurar Profesores en la tabla Usuario
# ==========================================================
profesores_datos = [
    ("imanol", "Imanol", "Uzuriaga"),
    ("silvina", "Silvina", "Trinchero"),
    ("joaquin", "Joaquín", "Calandri"),
    ("matias", "Matías", "Cardozo"),
    ("julia", "Julia", "Tramonti"),
    ("victoria", "Victoria", "Bargas"),
    ("andrea", "Andrea", "Adalid"),
]

for username, nombre, apellido in profesores_datos:
    u, created = Usuario.objects.get_or_create(
        username=username,
        defaults={
            "first_name": nombre,
            "last_name": apellido,
            "rol": "entrenador",
            "is_staff": True,
            "is_active": True,
        }
    )
    if not created:
        u.first_name = nombre
        u.last_name = apellido
        u.rol = "entrenador"
        u.is_staff = True
        u.is_active = True
    u.set_password("123")
    u.save()

# ==========================================================
# 2. Cargar Planes con precio en defaults
# ==========================================================
planes_datos = [
    ("Musculación (Pase Completo)", 60000, 30, "Incluye musculación y clases."),
    ("Pase Clases", 45000, 30, "Acceso a clases grupales: Funcional, Spinning, Abdominales, Cardio y Zumba."),
    ("Pilates - 1 vez por semana", 35000, 30, "1 clase semanal de Pilates."),
    ("Pilates - 2 veces por semana", 42000, 30, "2 clases semanales de Pilates."),
    ("Pilates - 3 veces por semana", 50000, 30, "3 clases semanales de Pilates."),
    ("Plan Familiar (x persona)", 50000, 30, "A partir de 3 personas abonando el mismo día."),
]

for nombre, precio, duracion, desc in planes_datos:
    defaults_dict = {"precio": precio}
    if hasattr(Plan, 'duracion_dias'):
        defaults_dict["duracion_dias"] = duracion
    if hasattr(Plan, 'descripcion'):
        defaults_dict["descripcion"] = desc

    p, created = Plan.objects.get_or_create(
        nombre=nombre,
        defaults=defaults_dict
    )
    if not created:
        p.precio = precio
        if hasattr(p, 'duracion_dias'):
            p.duracion_dias = duracion
        if hasattr(p, 'descripcion'):
            p.descripcion = desc
        p.save()

# ==========================================================
# 3. Cargar Actividades / Disciplinas
# ==========================================================
actividades_datos = [
    ("Musculación", "Acceso de Lun a Vie de 7 a 22 hs y Sáb de 9 a 13 hs con profesores en sala.", False),
    ("Funcional", "Lunes, Miércoles y Viernes 18:00 hs (Prof. Imanol Uzuriaga).", True),
    ("Spinning", "Lunes, Miércoles y Viernes 19:00 hs (Prof. Julia Tramonti).", True),
    ("Abdominales", "Lunes, Miércoles y Viernes 20:00 hs (Prof. Julia Tramonti).", True),
    ("Funcional + Cardio", "Martes y Jueves 18:00 hs (Prof. Imanol Uzuriaga).", True),
    ("Zumba", "Lunes, Martes y Jueves 19:00 hs (Prof. Victoria Bargas).", True),
    ("Pilates", "Lun 9-11hs, Mié 11-13hs, Vie 16-18hs (Prof. Andrea Adalid).", True),
]

for nombre, desc, req_reserva in actividades_datos:
    defaults_act = {"descripcion": desc}
    if hasattr(Actividad, 'requiere_reserva'):
        defaults_act["requiere_reserva"] = req_reserva

    act, created = Actividad.objects.get_or_create(
        nombre=nombre,
        defaults=defaults_act
    )
    if not created:
        act.descripcion = desc
        if hasattr(act, 'requiere_reserva'):
            act.requiere_reserva = req_reserva
        act.save()

print("\n" + "="*55)
print("✅ DATOS INICIALES DE GYMTRACK CARGADOS EXITOSAMENTE")
print(f"• Profesores registrados: {len(profesores_datos)}")
print(f"• Planes y aranceles cargados: {len(planes_datos)}")
print(f"• Disciplinas dadas de alta: {len(actividades_datos)}")
print("="*55 + "\n")
