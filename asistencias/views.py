# asistencias/views.py
from datetime import datetime, time
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from usuarios.models import Usuario
from socios.models import Socio
from asistencias.models import Asistencia

try:
    from reservas.models import Reserva
except ImportError:
    Reserva = None

def validar_ingreso_socio(request, dni):
    hoy = timezone.localdate()
    inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
    fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

    try:
        usuario_socio = Usuario.objects.get(username=dni, rol='socio')
        socio = getattr(usuario_socio, 'perfil_socio', None) or Socio.objects.get(
            usuario=usuario_socio
        )
    except (Usuario.DoesNotExist, Exception):
        messages.error(request, f'No existe ningún socio con DNI {dni}.')
        return redirect('dashboard')

    # 1. Semáforo financiero obligatorio
    if getattr(socio, 'estado_cuenta', 'VERDE').upper() != 'VERDE':
        messages.error(
            request,
            f'Acceso DENEGADO: {usuario_socio.first_name} adeuda cuota (Rojo).',
        )
        return redirect('dashboard')

    # 2. Consultar si ya tiene ingresos hoy
    asistencias_hoy = Asistencia.objects.filter(
        socio=socio, fecha_hora__range=(inicio_dia, fin_dia)
    )

    if not asistencias_hoy.exists():
        # Primer ingreso del día: Libre (Musculación / Sala)
        Asistencia.objects.create(socio=socio, fecha_hora=timezone.now())
        messages.success(
            request,
            f'Acceso Libre: Ingreso registrado para {usuario_socio.first_name} {usuario_socio.last_name}.',
        )
        return redirect('dashboard')

    # 3. Si ya ingresó hoy, verificar reservas para turnos/clases
    reserva_hoy = None
    if Reserva:
        reserva_hoy = (
            Reserva.objects.filter(
                socio=socio, fecha=hoy, estado__in=['confirmada', 'activa']
            )
            .select_related('horario__actividad')
            .first()
        )

    # Permitir si la cantidad de ingresos es menor al cupo de accesos válidos del día (1 libre + 1 por reserva)
    total_accesos_permitidos = 1 + (1 if reserva_hoy else 0)

    if asistencias_hoy.count() < total_accesos_permitidos and reserva_hoy:
        nombre_actividad = reserva_hoy.horario.actividad.nombre
        hora_turno = reserva_hoy.horario.hora_inicio.strftime('%H:%M')

        # Registrar el segundo ingreso específico para la clase
        Asistencia.objects.create(socio=socio, fecha_hora=timezone.now())

        # Si el modelo tiene estado de asistencia en la reserva, marcarla como asistida
        if hasattr(reserva_hoy, 'estado'):
            reserva_hoy.estado = 'asistida'
            reserva_hoy.save()

        messages.success(
            request,
            f'Acceso Concedido: Turno de {nombre_actividad} ({hora_turno} hs) para {usuario_socio.first_name}.',
        )
    else:
        primer_ingreso = asistencias_hoy.first().fecha_hora.strftime('%H:%M')
        if reserva_hoy:
            messages.warning(
                request,
                f'{usuario_socio.first_name} ya completó su asistencia a musculación ({primer_ingreso} hs) y a su clase reservada.',
            )
        else:
            messages.warning(
                request,
                f'{usuario_socio.first_name} ya ingresó hoy ({primer_ingreso} hs) y no tiene reserva activa para otra actividad.',
            )

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

        try:
            # 1. El DNI se busca en username para los socios
            usuario_socio = Usuario.objects.get(username=dni, rol='socio')

            # 2. Obtener el perfil del socio
            if hasattr(usuario_socio, 'perfil_socio'):
                socio = usuario_socio.perfil_socio
            else:
                socio = Socio.objects.get(usuario=usuario_socio)

            # 3. Comprobar semáforo de estado de cuenta
            if getattr(socio, 'estado_cuenta', 'VERDE').upper() == 'VERDE':
                # Evitar duplicar asistencia si ya ingresó hoy
                ya_marco = Asistencia.objects.filter(
                    socio=socio,
                    fecha_hora__range=(inicio_dia, fin_dia)
                ).exists()

                if not ya_marco:
                    Asistencia.objects.create(
                        socio=socio,
                        fecha_hora=timezone.now()
                    )
                    messages.success(
                        request,
                        f"Acceso CONCEDIDO: {usuario_socio.first_name} {usuario_socio.last_name} (Al Día)."
                    )
                else:
                    messages.warning(
                        request,
                        f"{usuario_socio.first_name} {usuario_socio.last_name} ya registró ingreso el día de hoy."
                    )
            else:
                messages.error(
                    request,
                    f"Acceso DENEGADO: {usuario_socio.first_name} figura con CUOTA VENCIDA (Rojo)."
                )

        except (Usuario.DoesNotExist, Socio.DoesNotExist):
            messages.error(request, f"No se encontró ningún socio registrado con el DNI {dni}.")

    return redirect('dashboard')