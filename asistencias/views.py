from datetime import datetime, time
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from usuarios.models import Usuario
from socios.models import Socio
from asistencias.models import Asistencia
from membresias.models import MembresiaSocio

try:
    from reservas.models import Reserva
except ImportError:
    Reserva = None


def _armar_perfil_socio_acceso(usuario_socio, socio, hoy, acceso_permitido=False, motivo=''):
    membresia_vigente = (
        MembresiaSocio.objects.filter(socio=socio, activa=True, fecha_fin__gte=hoy)
        .select_related('plan')
        .order_by('-fecha_fin')
        .first()
    )
    ultima_membresia = (
        membresia_vigente
        or MembresiaSocio.objects.filter(socio=socio).select_related('plan').order_by('-fecha_fin').first()
    )
    esta_al_dia = bool(membresia_vigente) and getattr(socio, 'estado_cuenta', 'VERDE') not in ['ROJO', 'VENCIDO']

    actividades_socio = []
    if Reserva:
        try:
            reservas_qs = Reserva.objects.filter(
                socio=socio, estado__in=['confirmada', 'activa', 'Confirmada', 'Activa']
            )
            for r in reservas_qs:
                act_r = getattr(r, 'actividad', None) or getattr(getattr(r, 'horario', None), 'actividad', None)
                if act_r and act_r.nombre not in actividades_socio:
                    actividades_socio.append(act_r.nombre)
        except Exception:
            pass

    historial_asistencias = [
        timezone.localtime(a.fecha_hora).strftime('%d/%m/%Y %H:%M hs')
        for a in Asistencia.objects.filter(socio=socio).order_by('-fecha_hora')[:5]
    ]

    nombre_completo = f"{usuario_socio.first_name} {usuario_socio.last_name}".strip() or usuario_socio.username
    iniciales = f"{usuario_socio.first_name[:1]}{usuario_socio.last_name[:1]}".upper() or usuario_socio.username[:2].upper()

    return {
        'nombre_completo': nombre_completo,
        'iniciales': iniciales,
        'foto_url': socio.foto.url if getattr(socio, 'foto', None) else None,
        'dni': usuario_socio.username,
        'email': usuario_socio.email or 'Sin email',
        'plan_nombre': (
            ultima_membresia.plan.nombre
            if (ultima_membresia and getattr(ultima_membresia, 'plan', None))
            else 'Sin Plan Asignado'
        ),
        'fecha_vencimiento': ultima_membresia.fecha_fin.strftime('%d/%m/%Y') if ultima_membresia else 'N/A',
        'al_dia': esta_al_dia,
        'estado_texto': 'AL DÍA' if esta_al_dia else 'CUOTA VENCIDA',
        'tipo_acceso': 'Acceso Libre (Musculación / Gimnasio)',
        'actividades': actividades_socio,
        'historial_asistencias': historial_asistencias,
        'acceso_permitido': acceso_permitido,
        'motivo': motivo,
    }


def validar_ingreso_socio(request, dni):
    hoy = timezone.localdate()
    inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
    fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))
    try:
        usuario_socio = Usuario.objects.get(username=dni, rol='socio')
        socio = getattr(usuario_socio, 'perfil_socio', None) or Socio.objects.get(usuario=usuario_socio)
    except (Usuario.DoesNotExist, Exception):
        messages.error(request, f'No existe ningún socio con DNI {dni}.')
        return redirect('dashboard')

    # 1. Semáforo
    if getattr(socio, 'estado_cuenta', 'VERDE').upper() != 'VERDE':
        request.session['ultimo_socio_acceso'] = _armar_perfil_socio_acceso(
            usuario_socio, socio, hoy, acceso_permitido=False, motivo='Cuota Vencida. Regularizar pago en caja.'
        )
        messages.error(
            request,
            f'Acceso DENEGADO: {usuario_socio.first_name} adeuda cuota (Rojo).',
        )
        return redirect('dashboard')

    # 2. Consultar ingresos hoy
    asistencias_hoy = Asistencia.objects.filter(
        socio=socio, fecha_hora__range=(inicio_dia, fin_dia)
    )
    if not asistencias_hoy.exists():
        Asistencia.objects.create(socio=socio, fecha_hora=timezone.now())
        request.session['ultimo_socio_acceso'] = _armar_perfil_socio_acceso(
            usuario_socio, socio, hoy, acceso_permitido=True, motivo='Primer ingreso del día registrado con éxito.'
        )
        messages.success(
            request,
            f'Acceso Libre: Ingreso registrado para {usuario_socio.first_name} {usuario_socio.last_name}.',
        )
        return redirect('dashboard')

    # 3. Verificar reservas para segundo ingreso del día
    reserva_hoy = None
    if Reserva:
        reserva_hoy = (
            Reserva.objects.filter(
                socio=socio, fecha=hoy, estado__in=['confirmada', 'activa']
            )
            .select_related('horario__actividad')
            .first()
        )
    total_accesos_permitidos = 1 + (1 if reserva_hoy else 0)
    if asistencias_hoy.count() < total_accesos_permitidos and reserva_hoy:
        nombre_actividad = reserva_hoy.horario.actividad.nombre
        hora_turno = reserva_hoy.horario.hora_inicio.strftime('%H:%M')
        Asistencia.objects.create(socio=socio, fecha_hora=timezone.now())
        if hasattr(reserva_hoy, 'estado'):
            reserva_hoy.estado = 'asistida'
            reserva_hoy.save()
        request.session['ultimo_socio_acceso'] = _armar_perfil_socio_acceso(
            usuario_socio, socio, hoy, acceso_permitido=True,
            motivo=f'Segundo ingreso validado por reserva en {nombre_actividad} ({hora_turno} hs).'
        )
        messages.success(
            request,
            f'Acceso Concedido: Turno de {nombre_actividad} ({hora_turno} hs) para {usuario_socio.first_name}.',
        )
    else:
        primer_ingreso = asistencias_hoy.first().fecha_hora.strftime('%H:%M')
        motivo_denegado = (
            f'{usuario_socio.first_name} ya completó su asistencia a musculación ({primer_ingreso} hs) y a su clase reservada.'
            if reserva_hoy
            else f'{usuario_socio.first_name} ya ingresó hoy ({primer_ingreso} hs) y no tiene reserva activa para otra actividad.'
        )
        request.session['ultimo_socio_acceso'] = _armar_perfil_socio_acceso(
            usuario_socio, socio, hoy, acceso_permitido=False, motivo=motivo_denegado
        )
        messages.warning(request, motivo_denegado)
    return redirect('dashboard')


@login_required
def registrar_asistencia(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado', 'admin')):
        return redirect('dashboard')

    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()
        hoy = timezone.localdate()
        inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
        fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

        usuario_socio = Usuario.objects.filter(username=dni, rol='socio', is_superuser=False).first()
        if not usuario_socio:
            messages.error(request, f"No se encontró ningún socio registrado con el DNI {dni}.")
            return redirect('dashboard')

        socio = (
            Socio.objects.filter(usuario=usuario_socio).first()
            or Socio.objects.filter(dni=dni).first()
        )
        if not socio:
            socio_kwargs = {'usuario': usuario_socio}
            if hasattr(Socio, 'dni'):
                socio_kwargs['dni'] = dni
            socio = Socio.objects.create(**socio_kwargs)

        membresia_vigente = (
            MembresiaSocio.objects.filter(socio=socio, activa=True, fecha_fin__gte=hoy)
            .order_by('-fecha_fin')
            .first()
        )
        esta_al_dia = bool(membresia_vigente) and getattr(socio, 'estado_cuenta', 'VERDE') not in ['ROJO', 'VENCIDO']

        if not esta_al_dia:
            request.session['ultimo_socio_acceso'] = _armar_perfil_socio_acceso(
                usuario_socio, socio, hoy, acceso_permitido=False, motivo="Cuota Vencida. Regularizar pago en caja."
            )
            messages.error(
                request,
                f"Acceso DENEGADO: {usuario_socio.first_name} figura con CUOTA VENCIDA (Rojo)."
            )
            return redirect('dashboard')

        ya_marco = Asistencia.objects.filter(
            socio=socio, fecha_hora__range=(inicio_dia, fin_dia)
        ).exists()

        if not ya_marco:
            Asistencia.objects.create(socio=socio, fecha_hora=timezone.now())
            request.session['ultimo_socio_acceso'] = _armar_perfil_socio_acceso(
                usuario_socio, socio, hoy, acceso_permitido=True, motivo="Primer ingreso del día registrado con éxito."
            )
            messages.success(
                request,
                f"Acceso CONCEDIDO: {usuario_socio.first_name} {usuario_socio.last_name} (Al Día)."
            )
        else:
            request.session['ultimo_socio_acceso'] = _armar_perfil_socio_acceso(
                usuario_socio, socio, hoy, acceso_permitido=False,
                motivo=f"{usuario_socio.first_name} {usuario_socio.last_name} ya registró ingreso el día de hoy."
            )
            messages.warning(
                request,
                f"{usuario_socio.first_name} {usuario_socio.last_name} ya registró ingreso el día de hoy."
            )

    return redirect('dashboard')