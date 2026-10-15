from datetime import datetime, time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from actividades.models import Actividad
from membresias.models import Plan
from usuarios.models import Usuario, AsistenciaEmpleado
from socios.models import Socio
from asistencias.models import Asistencia

try:
    from rutinas.models import Rutina
except ImportError:
    Rutina = None

try:
    from reservas.models import Reserva
except ImportError:
    Reserva = None

try:
    from pagos.models import Pago
except ImportError:
    Pago = None


# ==========================================================
# 🌐 1. PORTADA PÚBLICA (LANDING PRINCIPAL)
# ==========================================================
def inicio_publico(request):
    """Landing comercial para visitantes anónimos"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    actividades = Actividad.objects.all()
    planes = Plan.objects.all()

    context = {
        'actividades': actividades,
        'membresias': planes,
    }
    return render(request, 'publico/index.html', context)


# ==========================================================
# 🚦 2. ENRUTADOR CENTRAL SEGÚN ROL (DASHBOARD)
# ==========================================================
@login_required
def dashboard(request):
    user = request.user

    # 1. Administrador (Superusuario o rol admin)
    if user.is_superuser or getattr(user, 'rol', None) == 'admin':
        total_socios = Usuario.objects.filter(rol='socio').count()
        total_empleados = Usuario.objects.filter(rol__in=['recepcion', 'entrenador', 'empleado']).count()
        total_actividades = Actividad.objects.count()

        hoy = timezone.localdate()
        total_mes = 0
        if Pago:
            total_mes = Pago.objects.filter(
                fecha_pago__year=hoy.year,
                fecha_pago__month=hoy.month
            ).aggregate(total=Sum('monto'))['total'] or 0

        context = {
            'total_socios': total_socios,
            'total_empleados': total_empleados,
            'total_actividades': total_actividades,
            'ingresos_mes': f"{total_mes:,.0f}".replace(',', '.'),
        }
        return render(request, 'admin/dashboard.html', context)

# 2. Empleado / Recepción / Mostrador Central
    elif getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado'):
        hoy = timezone.localdate()
        inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
        fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

        # Manejo de acciones sobre profesores
        if request.method == 'POST' and 'accion_profesor' in request.POST:
            accion_p = request.POST.get('accion_profesor')
            profe_id = request.POST.get('profesor_id')
            profe_obj = get_object_or_404(Usuario, id=profe_id)

            if accion_p == 'iniciar':
                dni_ingresado = request.POST.get('dni_verif', '').strip()
                pass_ingresada = request.POST.get('password_verif', '').strip()

                # Validación de seguridad: DNI y contraseña del profesor
                dni_correcto = (profe_obj.username == dni_ingresado) or (getattr(profe_obj, 'dni', None) == dni_ingresado)

                if not dni_correcto:
                    messages.error(request, f"DNI incorrecto para {profe_obj.first_name}. Verifique los datos.")
                elif not profe_obj.check_password(pass_ingresada):
                    messages.error(request, f"Contraseña incorrecta para {profe_obj.first_name}.")
                else:
                    # Validar si ya tiene un turno abierto hoy
                    turno_activo = AsistenciaEmpleado.objects.filter(
                        empleado=profe_obj,
                        hora_salida__isnull=True,
                        hora_entrada__range=(inicio_dia, fin_dia)
                    ).first()

                    if not turno_activo:
                        AsistenciaEmpleado.objects.create(empleado=profe_obj, hora_entrada=timezone.now())
                        messages.success(request, f"Turno iniciado correctamente para {profe_obj.first_name} {profe_obj.last_name}.")
                    else:
                        messages.warning(request, f"{profe_obj.first_name} ya tiene un turno en curso.")

            elif accion_p == 'cortar':
                turno_activo = AsistenciaEmpleado.objects.filter(
                    empleado=profe_obj,
                    hora_salida__isnull=True,
                    hora_entrada__range=(inicio_dia, fin_dia)
                ).first()

                if turno_activo:
                    turno_activo.hora_salida = timezone.now()
                    turno_activo.save()
                    messages.success(request, f"Turno finalizado para {profe_obj.first_name}. Duración: {turno_activo.horas_trabajadas}.")

            return redirect('dashboard')

        # Grilla de profesores con sus actividades y horarios asignados
        profesores_datos_info = [
            {
                'username': 'imanol',
                'rol_desc': 'Musculación & Clases',
                'detalle': 'Musculación: Lunes a Viernes 7-9 hs y 19-22 hs y Sábado 9-13hs | Funcional + Cardio lunes a viernes 18 hs)'
            },
            {
                'username': 'silvina',
                'rol_desc': 'Musculación',
                'detalle': 'Lunes a Viernes de 09 a 15 hs'
            },
            {
                'username': 'joaquin',
                'rol_desc': 'Musculación',
                'detalle': 'Lunes, Miércoles y Viernes de 15 a 19 hs'
            },
            {
                'username': 'matias',
                'rol_desc': 'Musculación',
                'detalle': 'Martes y Jueves de 15 a 19 hs'
            },
            {
                'username': 'julia',
                'rol_desc': 'Spinning & Abdominales',
                'detalle': 'Lunes, Miércoles y Viernes: Spinning 19 hs y Abdominales 20 hs'
            },
            {
                'username': 'victoria',
                'rol_desc': 'Zumba',
                'detalle': 'Lunes, Martes y Jueves a las 19 hs'
            },
            {
                'username': 'andrea',
                'rol_desc': 'Pilates Reformer',
                'detalle': 'Lunes 9-11 hs, Miércoles 11-13 hs y Viernes 16-18 hs'
            },
        ]

        profesores_cards = []
        for info in profesores_datos_info:
            profe = Usuario.objects.filter(username=info['username']).first()
            if profe:
                # Turno del día
                turno_hoy = AsistenciaEmpleado.objects.filter(
                    empleado=profe,
                    hora_entrada__range=(inicio_dia, fin_dia)
                ).order_by('-hora_entrada').first()

                en_turno = turno_hoy and turno_hoy.hora_salida is None

                # Historial de turnos cerrados para estadísticas
                historial_turnos = AsistenciaEmpleado.objects.filter(
                    empleado=profe
                ).order_by('-hora_entrada')[:15]

                # Cálculo de total de minutos y horas acumuladas
                minutos_totales = 0
                for t in historial_turnos:
                    if t.hora_salida:
                        duracion = t.hora_salida - t.hora_entrada
                        minutos_totales += int(duracion.total_seconds() // 60)

                horas_acumuladas = f"{minutos_totales // 60}h {minutos_totales % 60}m"

                profesores_cards.append({
                    'usuario': profe,
                    'rol_desc': info['rol_desc'],
                    'detalle': info['detalle'],
                    'en_turno': en_turno,
                    'turno': turno_hoy,
                    'historial': historial_turnos,
                    'horas_acumuladas': horas_acumuladas,
                    'total_turnos': historial_turnos.count(),
                })

        # Asistencias de socios registradas en recepción
        asistencias_qs = Asistencia.objects.filter(
            fecha_hora__range=(inicio_dia, fin_dia)
        ).select_related('socio__usuario').order_by('-fecha_hora')

        context = {
            'asistencias_hoy': asistencias_qs.count(),
            'ultimas_asistencias': asistencias_qs[:10],
            'total_socios': Usuario.objects.filter(rol='socio').count(),
            'total_actividades': Actividad.objects.count(),
            'profesores_cards': profesores_cards,
        }
        return render(request, 'empleado/dashboard.html', context)
    
# 3. Socio (Portal con 3 Botones Principales)
    else:
        if hasattr(user, 'perfil_socio') and user.perfil_socio:
            socio_obj = user.perfil_socio
        else:
            socio_obj = Socio.objects.filter(usuario=user).first()
            if not socio_obj:
                socio_obj = Socio.objects.create(usuario=user)

        estado_cuenta = getattr(socio_obj, 'estado_cuenta', getattr(user, 'estado_cuenta', 'VERDE')).upper()

        # Importamos los modelos de rutinas
        from rutinas.models import Rutina, DiaEntrenamiento, Ejercicio

        # Obtener o crear la rutina personalizada del socio
        rutina_custom = Rutina.objects.filter(socio=user, tipo='personalizada').first()
        if not rutina_custom:
            rutina_custom = Rutina.objects.create(socio=user, tipo='personalizada', nombre='Mi Rutina Semanal')

        # Acciones POST: Perfil, Clave, o Gestión de Rutinas
        if request.method == 'POST':
            accion = request.POST.get('accion')

            # --- GESTIÓN DE RUTINA EN BASE DE DATOS ---
            if accion == 'agregar_ejercicio_custom':
                nombre_dia = request.POST.get('dia', 'lunes').lower()
                nombre_ejercicio = request.POST.get('nombre_ejercicio', '').strip()
                series_reps = request.POST.get('repeticiones', '').strip()

                if nombre_ejercicio:
                    # Mapeo de número de día
                    dias_map = {
                        'lunes': 1, 'martes': 2, 'miercoles': 3, 'jueves': 4,
                        'viernes': 5, 'sabado': 6, 'domingo': 7
                    }
                    num_dia = dias_map.get(nombre_dia, 1)

                    dia_obj, _ = DiaEntrenamiento.objects.get_or_create(
                        rutina=rutina_custom,
                        nombre_dia=nombre_dia,
                        defaults={'numero_dia': num_dia, 'enfoque': 'Entrenamiento'}
                    )

                    Ejercicio.objects.create(
                        dia=dia_obj,
                        nombre=nombre_ejercicio,
                        repeticiones=series_reps or '4 series x 10-12 reps'
                    )
                    messages.success(request, f'Ejercicio agregado al día {nombre_dia.capitalize()}.')
                return redirect('dashboard')

            elif accion == 'eliminar_ejercicio_custom':
                ejercicio_id = request.POST.get('ejercicio_id')
                # Verificamos que el ejercicio pertenezca a la rutina de este socio antes de borrar
                Ejercicio.objects.filter(
                    id=ejercicio_id,
                    dia__rutina__socio=user
                ).delete()
                messages.success(request, 'Ejercicio eliminado de tu rutina.')
                return redirect('dashboard')

            # --- ACTUALIZACIÓN DE PERFIL ---
            elif accion == 'actualizar_perfil':
                user.first_name = request.POST.get('first_name', '').strip()
                user.last_name = request.POST.get('last_name', '').strip()
                user.email = request.POST.get('email', '').strip()
                if hasattr(user, 'telefono'):
                    user.telefono = request.POST.get('telefono', '').strip()
                user.save()
                messages.success(request, 'Tus datos fueron actualizados correctamente.')
                return redirect('dashboard')

            # --- CAMBIO DE CONTRASEÑA ---
            elif accion == 'cambiar_password':
                pass_actual = request.POST.get('pass_actual')
                pass_nueva = request.POST.get('pass_nueva')
                pass_confirmar = request.POST.get('pass_confirmar')

                if not user.check_password(pass_actual):
                    messages.error(request, 'La contraseña actual ingresada es incorrecta.')
                elif pass_nueva != pass_confirmar:
                    messages.error(request, 'Las nuevas contraseñas no coinciden.')
                elif len(pass_nueva) < 3:
                    messages.error(request, 'La nueva contraseña debe tener al menos 3 caracteres.')
                else:
                    user.set_password(pass_nueva)
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, '¡Tu contraseña ha sido cambiada con éxito!')
                return redirect('dashboard')

        # Clasificación de Actividades
        todas_actividades = Actividad.objects.all()
        actividades_anotadas = []
        actividades_disponibles = []

        if hasattr(socio_obj, 'actividades') and socio_obj.actividades.exists():
            actividades_anotadas = list(socio_obj.actividades.all())
            actividades_disponibles = [a for a in todas_actividades if a not in actividades_anotadas]
        elif Reserva:
            reservas = Reserva.objects.filter(socio=socio_obj)
            ids_anotadas = [r.horario.actividad_id for r in reservas if hasattr(r, 'horario') and r.horario]
            actividades_anotadas = [a for a in todas_actividades if a.id in ids_anotadas]
            actividades_disponibles = [a for a in todas_actividades if a.id not in ids_anotadas]
        else:
            actividades_anotadas = list(todas_actividades[:1])
            actividades_disponibles = list(todas_actividades[1:])

        # Historial de pagos
        pagos = []
        if Pago:
            pagos = Pago.objects.filter(socio=socio_obj).order_by('-fecha_pago')

        # Agrupamos los ejercicios de la base de datos por día de la semana
        rutina_semanal = {
            'lunes': [], 'martes': [], 'miercoles': [], 'jueves': [],
            'viernes': [], 'sabado': [], 'domingo': []
        }
        for dia in rutina_custom.dias.prefetch_related('ejercicios').all():
            clave_dia = dia.nombre_dia.lower()
            if clave_dia in rutina_semanal:
                rutina_semanal[clave_dia] = dia.ejercicios.all()

        context = {
            'socio': socio_obj,
            'estado_cuenta': estado_cuenta,
            'actividades_anotadas': actividades_anotadas,
            'actividades_disponibles': actividades_disponibles,
            'pagos': pagos,
            'rutina_semanal': rutina_semanal,
        }
        return render(request, 'socio/dashboard.html', context)
    
# ==========================================================
# 👥 3. ADMINISTRACIÓN DE EMPLEADOS (ADMIN)
# ==========================================================
@login_required
def admin_empleados(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'toggle_baja':
            emp_id = request.POST.get('empleado_id')
            empleado = get_object_or_404(Usuario, id=emp_id)
            if empleado == user:
                messages.error(request, 'No podés darte de baja a vos mismo.')
            else:
                empleado.is_active = not empleado.is_active
                empleado.save()
                estado = "activo" if empleado.is_active else "dado de baja"
                messages.success(request, f'El empleado {empleado.username} ahora está {estado}.')
            return redirect('admin_empleados')

        elif accion == 'alta':
            username = request.POST.get('username', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            email = request.POST.get('email', '').strip()
            rol = request.POST.get('rol', 'recepcion').strip()
            password = request.POST.get('password', '').strip() or '123'

            if Usuario.objects.filter(username=username).exists():
                messages.error(request, f'El usuario {username} ya existe.')
            else:
                nuevo_emp = Usuario.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=nombre,
                    last_name=apellido
                )
                nuevo_emp.rol = rol
                nuevo_emp.is_staff = True
                nuevo_emp.save()
                messages.success(request, f'Empleado {nombre} {apellido} creado con éxito.')
            return redirect('admin_empleados')

    query = request.GET.get('q', '').strip()
    filtro_rol = request.GET.get('rol', 'todos')

    empleados = Usuario.objects.filter(rol__in=['recepcion', 'entrenador', 'admin', 'empleado']).order_by('-date_joined')

    if query:
        empleados = empleados.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    if filtro_rol != 'todos':
        empleados = empleados.filter(rol=filtro_rol)

    context = {
        'empleados': empleados,
        'query': query,
        'filtro_rol': filtro_rol,
        'total_empleados': empleados.count(),
    }
    return render(request, 'admin/empleados.html', context)


# ==========================================================
# ⏱️ 4. PERFIL DEL EMPLEADO Y FICHAJE LABORAL
# ==========================================================
@login_required
def mi_perfil_empleado(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado')):
        return redirect('dashboard')

    hoy = timezone.localdate()
    inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
    fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

    turno_actual = AsistenciaEmpleado.objects.filter(
        empleado=user,
        hora_salida__isnull=True,
        hora_entrada__range=(inicio_dia, fin_dia)
    ).first()

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'entrada':
            if not turno_actual:
                AsistenciaEmpleado.objects.create(empleado=user, hora_entrada=timezone.now())
                messages.success(request, 'Entrada registrada. ¡Buen turno!')
            else:
                messages.warning(request, 'Ya tenés un turno en curso.')
            return redirect('mi_perfil_empleado')

        elif accion == 'salida':
            if turno_actual:
                turno_actual.hora_salida = timezone.now()
                turno_actual.save()
                messages.success(request, f'Salida registrada. Total: {turno_actual.horas_trabajadas}.')
            return redirect('mi_perfil_empleado')

    historial_turnos = AsistenciaEmpleado.objects.filter(empleado=user).order_by('-hora_entrada')[:15]

    context = {
        'empleado': user,
        'turno_actual': turno_actual,
        'historial_turnos': historial_turnos,
    }
    return render(request, 'empleado/perfil.html', context)