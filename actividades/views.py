from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from actividades.models import Actividad
from usuarios.models import Usuario

try:
    from reservas.models import Reserva
except ImportError:
    Reserva = None


# ==============================================================================
# 1. GESTIÓN DE ACTIVIDADES (ADMIN)
# ==============================================================================
@login_required
def admin_actividades(request):
    """Permite al admin ver, crear, pausar y eliminar disciplinas del gimnasio"""
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'alta':
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            if nombre:
                Actividad.objects.create(nombre=nombre, descripcion=descripcion)
                messages.success(request, f'Actividad "{nombre}" agregada correctamente.')
            else:
                messages.error(request, 'El nombre de la actividad es obligatorio.')
            return redirect('admin_actividades')
        elif accion == 'eliminar':
            act_id = request.POST.get('actividad_id')
            actividad = get_object_or_404(Actividad, id=act_id)
            nombre_eliminado = actividad.nombre
            actividad.delete()
            messages.success(request, f'Actividad "{nombre_eliminado}" eliminada.')
            return redirect('admin_actividades')
        elif accion in ['pausar', 'toggle_estado', 'toggle_baja']:
            act_id = request.POST.get('actividad_id')
            actividad = get_object_or_404(Actividad, id=act_id)
            actividad.activa = not actividad.activa
            actividad.save()
            estado_str = "activada" if actividad.activa else "pausada"
            messages.success(request, f'Actividad "{actividad.nombre}" {estado_str} correctamente.')
            return redirect('admin_actividades')

    actividades = Actividad.objects.all().order_by('nombre')
    context = {
        'actividades': actividades,
        'total_actividades': actividades.count(),
    }
    return render(request, 'admin/actividades.html', context)


# ==============================================================================
# 2. CLASES Y RESERVAS (EMPLEADO / RECEPCIÓN)
# ==============================================================================
@login_required
def actividades_empleado(request):
    """Permite al recepcionista consultar los socios anotados en cada clase"""
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado', 'admin')):
        return redirect('dashboard')

    actividades = Actividad.objects.filter(activa=True).order_by('nombre')
    actividad_seleccionada_id = request.GET.get('actividad_id')
    socios_inscriptos = []
    actividad_actual = None

    if actividad_seleccionada_id:
        actividad_actual = Actividad.objects.filter(id=actividad_seleccionada_id).first()
        if actividad_actual:
            if Reserva:
                reservas = Reserva.objects.filter(
                    horario__actividad=actividad_actual
                ).select_related('socio__usuario')
                socios_inscriptos = [r.socio.usuario for r in reservas]
            elif hasattr(actividad_actual, 'socios'):
                socios_inscriptos = [s.usuario for s in actividad_actual.socios.all()]
            else:
                socios_inscriptos = Usuario.objects.filter(rol='socio')[:8]

    context = {
        'actividades': actividades,
        'actividad_actual': actividad_actual,
        'socios_inscriptos': socios_inscriptos,
        'total_inscriptos': len(socios_inscriptos),
    }
    return render(request, 'empleado/actividades.html', context)


# ==============================================================================
# 3. DISCIPLINAS, CRONOGRAMA Y RESERVAS (PANTALLA empleado/reservas.html)
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
