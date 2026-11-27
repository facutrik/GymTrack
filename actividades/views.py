from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from actividades.models import Actividad
from usuarios.models import Usuario

try:
    from reservas.models import Reserva
except ImportError:
    Reserva = None


# ==============================================================================
# DISCIPLINAS, CRONOGRAMA Y RESERVAS (PANTALLA empleado/reservas.html)
# ==============================================================================
# Turnos de los profesores en la sala de musculación (usuario: horario)
HORARIOS_SALA = {
    'imanol': 'Lun a Vie de 7 a 9 y de 19 a 22 hs · Sáb de 9 a 13 hs',
    'silvina': 'Lun a Vie de 9 a 15 hs',
    'joaquin': 'Lun, Mié y Vie de 15 a 19 hs',
    'matias': 'Mar y Jue de 15 a 19 hs',
}


@login_required
def reservas_empleado(request):
    """Muestra disciplinas activas, cronograma y cantidad de anotados para recepción"""
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado', 'admin')):
        return redirect('dashboard')

    sala, clases = [], []
    for act in Actividad.objects.filter(activa=True).order_by('nombre'):
        if act.sin_turno:
            sala.append(act)
            continue

        anotados = []
        if Reserva:
            reservas = (
                Reserva.objects.filter(clase__actividad=act, estado='confirmada')
                .select_related('socio__usuario')
                .order_by('socio__usuario__last_name', 'socio__usuario__first_name')
            )
            for socio in dict.fromkeys(r.socio for r in reservas):
                usuario = socio.usuario
                anotados.append({
                    'nombre': (usuario.get_full_name() or usuario.username) if usuario else str(socio),
                    'dni': usuario.username if usuario else socio.dni,
                })

        item = {'actividad': act, 'anotados': anotados, 'total': len(anotados), 'cupo': None}
        if act.requiere_reserva and Reserva:
            item['cupo'] = Reserva.cupo_de(act)
            item['libres'] = max(item['cupo'] - item['total'], 0)
            item['porcentaje'] = min(round(item['total'] * 100 / item['cupo']), 100)
        clases.append(item)

    profesores_sala = []
    if sala:
        usuarios = {u.username: u for u in Usuario.objects.filter(username__in=HORARIOS_SALA, is_active=True)}
        profesores_sala = [
            {'nombre': usuarios[u].get_full_name() or u, 'horario': horario}
            for u, horario in HORARIOS_SALA.items() if u in usuarios
        ]

    context = {
        'sala': sala,
        'profesores_sala': profesores_sala,
        'clases': clases,
        'total_inscripciones': sum(c['total'] for c in clases),
        'clases_completas': sum(1 for c in clases if c['cupo'] and not c['libres']),
    }
    return render(request, 'empleado/reservas.html', context)
