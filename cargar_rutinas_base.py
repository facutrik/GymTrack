import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymtrack.settings')
django.setup()

from usuarios.models import Usuario
from rutinas.models import Rutina, DiaEntrenamiento, Ejercicio

PLANES_BASE = [
    {
        'nombre': 'Adaptación',
        'dias': [
            {
                'nombre_dia': 'Día 1 - Torso y Brazos Base',
                'ejercicios': [
                    ('Banco plano en máquina o mancuernas', 3, '12-15 reps', '60-90s'),
                    ('Dorsalera agarre neutro', 3, '12-15 reps', '60-90s'),
                    ('Remo sentado en polea baja', 3, '12-15 reps', '60-90s'),
                    ('Vuelos laterales con mancuernas', 3, '12-15 reps', '60s'),
                    ('Extensión de tríceps en polea con soga', 2, '12-15 reps', '60s'),
                    ('Bíceps con mancuernas alternado', 2, '12-15 reps', '60s'),
                ]
            },
            {
                'nombre_dia': 'Día 2 - Piernas y Zona Media',
                'ejercicios': [
                    ('Aductores en máquina', 3, '12-15 reps', '60s'),
                    ('Prensa inclinada 45°', 3, '12-15 reps', '60-90s'),
                    ('Cuádriceps en sillón', 3, '12-15 reps', '60s'),
                    ('Femorales acostado en camilla', 3, '12-15 reps', '60s'),
                    ('Gemelo parado en máquina', 3, '15 reps', '60s'),
                    ('Plancha abdominal', 3, '30-40s', '60s'),
                ]
            },
            {
                'nombre_dia': 'Día 3 - Full Body y Postura',
                'ejercicios': [
                    ('Sentadilla goblet con mancuerna', 3, '12-15 reps', '60-90s'),
                    ('Inclinado con mancuernas', 3, '12-15 reps', '60-90s'),
                    ('Dorsalera con barra', 3, '12-15 reps', '60-90s'),
                    ('Face pull en polea', 3, '12-15 reps', '60s'),
                    ('Martillo con soga en polea', 2, '12-15 reps', '60s'),
                    ('Crunch abdominal en colchoneta', 3, '15 reps', '60s'),
                ]
            },
        ]
    },
    {
        'nombre': 'Hipertrofia',
        'dias': [
            {
                'nombre_dia': 'Día 1 - Pecho, Hombros y Tríceps',
                'ejercicios': [
                    ('Banco plano con barra', 3, '6-8 reps', '90-120s'),
                    ('Inclinado con mancuernas', 3, '8-12 reps', '90-120s'),
                    ('Cruces en polea', 3, '10-15 reps', '90s'),
                    ('Vuelos laterales en polea', 3, '10-15 reps', '90s'),
                    ('Press francés con barra W', 3, '10-12 reps', '90s'),
                    ('Extensión de tríceps en polea alta con soga', 3, '8-12 reps', '90s'),
                    ('Extensión trasnuca con soga', 3, '10-15 reps', '90s'),
                ]
            },
            {
                'nombre_dia': 'Día 2 - Piernas',
                'ejercicios': [
                    ('Aductores en máquina', 3, '8-12 reps', '90s'),
                    ('Sentadilla libre con barra', 3, '8-10 reps', '120s'),
                    ('Peso muerto con barra', 3, '8-10 reps', '120s'),
                    ('Cuádriceps en sillón', 3, '10-15 reps', '90s'),
                    ('Femorales acostado en camilla', 3, '10-12 reps', '90s'),
                    ('Gemelo parado', 3, '10-15 reps', '90s'),
                ]
            },
            {
                'nombre_dia': 'Día 3 - Espalda, Posterior y Bíceps',
                'ejercicios': [
                    ('Dorsalera con barra', 3, '8-10 reps', '90-120s'),
                    ('Remo T', 3, '8-12 reps', '90-120s'),
                    ('Dorsalera agarre neutro', 3, '8-12 reps', '90s'),
                    ('Pullover con soga', 3, '10-15 reps', '90s'),
                    ('Face pull en polea', 3, '10-15 reps', '90s'),
                    ('Bíceps con barra W', 3, '8-12 reps', '90s'),
                    ('Bíceps sentado con mancuernas', 3, '10-12 reps', '90s'),
                    ('Martillo con soga', 3, '10-12 reps', '90s'),
                ]
            },
        ]
    },
    {
        'nombre': 'Fuerza',
        'dias': [
            {
                'nombre_dia': 'Día 1 - Empuje Pesado (Pecho, Hombro y Tríceps)',
                'ejercicios': [
                    ('Banco plano con barra', 4, '4-6 reps', '150-180s'),
                    ('Press militar de pie con barra', 4, '5-6 reps', '150s'),
                    ('Inclinado con mancuernas pesadas', 3, '6-8 reps', '120s'),
                    ('Fondos en paralelas lastrados', 3, '6-8 reps', '120s'),
                    ('Press francés pesado', 3, '6-8 reps', '120s'),
                ]
            },
            {
                'nombre_dia': 'Día 2 - Piernas Pesado (Sentadilla y Peso Muerto)',
                'ejercicios': [
                    ('Sentadilla trasera con barra', 4, '4-6 reps', '180s'),
                    ('Peso muerto convencional con barra', 4, '3-5 reps', '180s'),
                    ('Prensa inclinada 45° pesada', 3, '6-8 reps', '150s'),
                    ('Femorales acostado en camilla', 3, '6-8 reps', '120s'),
                    ('Gemelo parado con carga', 3, '8-10 reps', '90s'),
                ]
            },
            {
                'nombre_dia': 'Día 3 - Tirón Pesado (Espalda y Bíceps)',
                'ejercicios': [
                    ('Remo T pesado', 4, '5-6 reps', '150s'),
                    ('Dorsalera con barra agarre amplio', 4, '6-8 reps', '150s'),
                    ('Remo agarre cerrado en polea', 3, '6-8 reps', '120s'),
                    ('Bíceps con barra W', 3, '6-8 reps', '120s'),
                    ('Martillo con soga pesado', 3, '6-8 reps', '90s'),
                ]
            },
        ]
    },
]

def cargar():
    usuario_base = Usuario.objects.filter(is_superuser=True).first() or Usuario.objects.first()
    if not usuario_base:
        print("No se encontró ningún usuario en la base de datos.")
        return

    for plan in PLANES_BASE:
        Rutina.objects.filter(nombre=plan['nombre'], tipo='gimnasio').delete()

        rutina_obj = Rutina.objects.create(
            socio=usuario_base,
            nombre=plan['nombre'],
            tipo='gimnasio'
        )
        for dia_data in plan['dias']:
            dia_obj = DiaEntrenamiento.objects.create(
                rutina=rutina_obj,
                nombre_dia=dia_data['nombre_dia']
            )
            for nombre_ej, series, reps, descanso in dia_data['ejercicios']:
                Ejercicio.objects.create(
                    dia=dia_obj,
                    nombre=nombre_ej,
                    series=series,
                    repeticiones=reps,
                    descanso=descanso
                )
        print(f"✅ Rutina '{plan['nombre']}' guardada en MySQL ({len(plan['dias'])} días).")

if __name__ == '__main__':
    cargar()