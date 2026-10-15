from datetime import datetime, time
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from usuarios.models import Usuario
from asistencias.models import Asistencia
from socios.models import Socio

try:
    from actividades.models import Actividad
except ImportError:
    Actividad = None


@login_required
def registrar_asistencia(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado', 'admin')):
        return redirect('dashboard')

    socio_obj = None
    usuario_socio = None
    estado_acceso = None
    asistencia_creada = None
    actividades_socio = []
    mensaje_error = None

    # Fecha y hora actual en zona horaria local
    ahora_local = timezone.localtime(timezone.now())
    dia_semana = ahora_local.weekday()  # 0=Lunes, 4=Viernes, 5=Sábado, 6=Domingo
    hora_actual = ahora_local.time()

    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()

        # -------------------------------------------------------------
        # 1. VALIDACIÓN DE HORARIO OPERATIVO
        # Lunes a Viernes: 07:00 a 22:00 | Sábados: 09:00 a 13:00
        # -------------------------------------------------------------
        horario_valido = False
        if 0 <= dia_semana <= 4:  # Lunes a Viernes
            if time(7, 0) <= hora_actual <= time(22, 0):
                horario_valido = True
            else:
                mensaje_error = "Fuera de horario operativo. Lunes a Viernes de 07:00 a 22:00 hs."
        elif dia_semana == 5:  # Sábado
            if time(9, 0) <= hora_actual <= time(13, 0):
                horario_valido = True
            else:
                mensaje_error = "Fuera de horario operativo. Sábados de 09:00 a 13:00 hs."
        else:  # Domingo cerrado
            mensaje_error = "El gimnasio se encuentra cerrado los días domingos."

        if not horario_valido:
            estado_acceso = 'fuera_de_horario'
        else:
            try:
                usuario_socio = Usuario.objects.get(username=dni, rol='socio')

                if hasattr(usuario_socio, 'perfil_socio') and usuario_socio.perfil_socio:
                    socio_obj = usuario_socio.perfil_socio
                else:
                    socio_obj = Socio.objects.filter(usuario=usuario_socio).first()
                    if not socio_obj:
                        socio_obj = Socio.objects.create(usuario=usuario_socio)

                # 2. VALIDAR CUOTA AL DÍA
                estado = getattr(socio_obj, 'estado_cuenta', 'VERDE')
                if not estado:
                    estado = getattr(usuario_socio, 'estado_cuenta', 'VERDE')

                if str(estado).upper() != 'VERDE':
                    estado_acceso = 'rojo'
                else:
                    # 3. VALIDAR 1 INGRESO POR DÍA
                    hoy = ahora_local.date()
                    inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
                    fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

                    ya_ingreso_hoy = Asistencia.objects.filter(
                        socio=socio_obj,
                        fecha_hora__range=(inicio_dia, fin_dia)
                    ).order_by('-fecha_hora').first()

                    if ya_ingreso_hoy:
                        estado_acceso = 'bloqueado_hoy'
                        asistencia_creada = ya_ingreso_hoy
                    else:
                        asistencia_creada = Asistencia.objects.create(
                            socio=socio_obj,
                            fecha_hora=timezone.now()
                        )
                        estado_acceso = 'verde'

                # Actividades habilitadas para la ficha
                if hasattr(socio_obj, 'actividades'):
                    actividades_socio = socio_obj.actividades.all()
                elif Actividad:
                    actividades_socio = Actividad.objects.all()[:2]

            except Usuario.DoesNotExist:
                estado_acceso = 'no_encontrado'

    # Consulta de asistencias de hoy para la tabla de fondo
    hoy = ahora_local.date()
    inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
    fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

    asistencias_qs = Asistencia.objects.filter(
        fecha_hora__range=(inicio_dia, fin_dia)
    ).select_related('socio__usuario').order_by('-fecha_hora')

    context = {
        'socio': socio_obj,
        'usuario_socio': usuario_socio,
        'estado_acceso': estado_acceso,
        'asistencia_creada': asistencia_creada,
        'actividades_socio': actividades_socio,
        'mensaje_error': mensaje_error,
        'asistencias_hoy': asistencias_qs.count(),
        'ultimas_asistencias': asistencias_qs[:10],
    }
    return render(request, 'empleado/dashboard.html', context)