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

    # 2. Empleado / Recepción / Entrenador
    elif getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado'):
        hoy = timezone.localdate()
        inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
        fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

        asistencias_qs = Asistencia.objects.filter(
            fecha_hora__range=(inicio_dia, fin_dia)
        ).select_related('socio__usuario').order_by('-fecha_hora')

        context = {
            'asistencias_hoy': asistencias_qs.count(),
            'ultimas_asistencias': asistencias_qs[:10],
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

        # Acciones POST en "Mi Perfil" (Datos y Contraseña)
        if request.method == 'POST':
            accion = request.POST.get('accion')

            if accion == 'actualizar_perfil':
                user.first_name = request.POST.get('first_name', '').strip()
                user.last_name = request.POST.get('last_name', '').strip()
                user.email = request.POST.get('email', '').strip()
                if hasattr(user, 'telefono'):
                    user.telefono = request.POST.get('telefono', '').strip()
                user.save()
                messages.success(request, 'Tus datos fueron actualizados correctamente.')
                return redirect('dashboard')

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

        # Clasificación de Actividades (Anotadas vs Disponibles)
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

        context = {
            'socio': socio_obj,
            'estado_cuenta': estado_cuenta,
            'actividades_anotadas': actividades_anotadas,
            'actividades_disponibles': actividades_disponibles,
            'pagos': pagos,
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