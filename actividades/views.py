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
@login_required
def reservas_empleado(request):
    """Muestra disciplinas activas, cronograma y cantidad de anotados para recepción"""
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado', 'admin')):
        return redirect('dashboard')

    hoy = timezone.localdate()
    actividades_db = Actividad.objects.filter(activa=True).order_by('nombre')
    disciplinas_detalle = []

    for act in actividades_db:
        horarios_lista = []
        clases_rel = (
            getattr(act, 'clases', None)
            or getattr(act, 'clase_set', None)
            or getattr(act, 'horarios', None)
        )
        clases_qs = clases_rel.all() if clases_rel else []

        for h in clases_qs:
            dias_str = getattr(h, 'dias', 'Lunes a Viernes')
            if hasattr(h, 'hora_inicio') and h.hora_inicio:
                hora_fin_str = (
                    h.hora_fin.strftime('%H:%M')
                    if getattr(h, 'hora_fin', None)
                    else ''
                )
                hora_str = (
                    f"{h.hora_inicio.strftime('%H:%M')} a {hora_fin_str} hs"
                    if hora_fin_str
                    else f"{h.hora_inicio.strftime('%H:%M')} hs"
                )
            else:
                hora_str = 'Consultar horario'

            profe = getattr(h, 'profesor', None)
            profe_str = (
                f"{profe.first_name} {profe.last_name}".strip() or profe.username
                if profe
                else 'A designar'
            )
            horarios_lista.append({
                'dias': dias_str,
                'horario': hora_str,
                'profesor': profe_str,
            })

        anotados_count = 0
        if Reserva:
            try:
                anotados_count = (
                    Reserva.objects.filter(
                        Q(horario__actividad=act) | Q(actividad=act),
                        estado__in=['confirmada', 'activa', 'Confirmada', 'Activa'],
                    )
                    .values('socio')
                    .distinct()
                    .count()
                )
            except Exception:
                try:
                    anotados_count = (
                        Reserva.objects.filter(
                            horario__actividad=act,
                            estado__in=['confirmada', 'activa', 'Confirmada', 'Activa'],
                        )
                        .values('socio')
                        .distinct()
                        .count()
                    )
                except Exception:
                    anotados_count = 0
        elif hasattr(act, 'reservas'):
            anotados_count = (
                act.reservas.filter(fecha=hoy, estado__in=['confirmada', 'activa'])
                .values('socio')
                .distinct()
                .count()
            )

        disciplinas_detalle.append({
            'actividad': act,
            'requiere_reserva': getattr(act, 'requiere_reserva', False),
            'horarios': horarios_lista,
            'anotados': anotados_count,
            'cupo_maximo': getattr(act, 'cupo_maximo', None) or getattr(act, 'cupo', None),
        })

    context = {
        'disciplinas_detalle': disciplinas_detalle,
    }
    return render(request, 'empleado/reservas.html', context)