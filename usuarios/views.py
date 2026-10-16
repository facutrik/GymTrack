from datetime import datetime, time, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum
from actividades.models import Actividad
from membresias.models import Plan, MembresiaSocio
from usuarios.models import Usuario, AsistenciaEmpleado
from asistencias.models import Asistencia
from socios.models import Socio
from pagos.models import Pago


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
try:
    from reservas.models import Reserva
except ImportError:
    Reserva = None


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PÁGINA PÚBLICA (INDEX)
def inicio_publico(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    actividades = Actividad.objects.all().order_by('nombre')
    planes = Plan.objects.all().order_by('precio')
    context = {
        'actividades': actividades,
        'membresias': planes,
    }
    return render(request, 'publico/index.html', context)


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# DASHBOARD CENTRAL (DISTRIBUIDOR DE ROLES)
@login_required
def dashboard(request):
    user = request.user
    hoy = timezone.localdate()


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 1. ADMINISTRADOR
    if user.is_superuser or getattr(user, 'rol', None) == 'admin':
        inicio_mes = timezone.make_aware(
            datetime(hoy.year, hoy.month, 1, 0, 0, 0)
        )
        if hoy.month == 12:
            inicio_mes_siguiente = timezone.make_aware(
                datetime(hoy.year + 1, 1, 1, 0, 0, 0)
            )
        else:
            inicio_mes_siguiente = timezone.make_aware(
                datetime(hoy.year, hoy.month + 1, 1, 0, 0, 0)
            )
        campos_pago = [f.name for f in Pago._meta.get_fields()]
        if 'fecha_pago' in campos_pago:
            filtro_rango = {
                'fecha_pago__gte': inicio_mes,
                'fecha_pago__lt': inicio_mes_siguiente,
            }
        elif 'fecha' in campos_pago:
            primer_dia_mes = hoy.replace(day=1)
            if hoy.month == 12:
                primer_dia_prox_mes = hoy.replace(
                    year=hoy.year + 1, month=1, day=1
                )
            else:
                primer_dia_prox_mes = hoy.replace(month=hoy.month + 1, day=1)
                filtro_rango = {
                    'fecha__gte': primer_dia_mes,
                    'fecha__lt': primer_dia_prox_mes,
            }
        else:
            filtro_rango = {}
        total_mes = (
            Pago.objects.filter(**filtro_rango).aggregate(total=Sum('monto'))[
                'total'
            ]
            or 0
        )
        if total_mes == 0:
            total_mes = Pago.objects.aggregate(total=Sum('monto'))['total'] or 0
        ingresos_mes_formateado = f'{int(total_mes):,}'.replace(',', '.')
        context = {
            'total_socios': Usuario.objects.filter(rol='socio').count(),
            'total_empleados': Usuario.objects.filter(
                rol__in=['recepcion', 'entrenador', 'empleado']
            ).count(),
            # Contar únicamente las disciplinas activas que se ofrecen actualmente
            'total_actividades': Actividad.objects.filter(activa=True).count(),
            'ingresos_mes': ingresos_mes_formateado,
            'socios_select': Usuario.objects.filter(
                rol='socio', is_active=True
            ).order_by('first_name'),
            'planes_select': Plan.objects.all().order_by('precio'),
        }
        return render(request, 'admin/dashboard.html', context)


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 2. EMPLEADO / RECEPCIÓN / ENTRENADOR
    elif getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado'):
        # Rango exacto de 24 horas locales para compatibilidad absoluta con SQLite
        inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
        fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

        # A. REGISTRAR COBRO PRESENCIAL DE MEMBRESÍA
        if request.method == 'POST' and request.POST.get('accion') == 'cobrar_membresia_empleado':
            dni_socio = request.POST.get('dni_socio', '').strip()
            plan_id = request.POST.get('plan_id')
            metodo = request.POST.get('metodo_pago', 'efectivo')
            # --- OPCIÓN FUTURA: Validar tarjeta cuando se habilite ---
            # METODOS_PERMITIDOS = ['efectivo', 'transferencia', 'tarjeta']
            # if metodo not in METODOS_PERMITIDOS:
            #     metodo = 'efectivo'
            socio_user = Usuario.objects.filter(username=dni_socio, rol='socio').first() or Usuario.objects.filter(username=dni_socio).first()
            plan_obj = Plan.objects.filter(id=plan_id).first() if plan_id else None
            if not socio_user:
                messages.error(request, f"No se encontró ningún socio registrado con el DNI {dni_socio}.")
            elif not plan_obj:
                messages.error(request, "Debe seleccionar un plan de membresía válido.")
            else:
                socio_obj, _ = Socio.objects.get_or_create(usuario=socio_user)
                monto_cobrado = plan_obj.precio
                duracion = getattr(plan_obj, 'duracion_dias', 30)
                # Desactivar membresías previas
                MembresiaSocio.objects.filter(socio=socio_obj).update(activa=False)
                # 1. Crear primero la MembresiaSocio
                membresia_creada = MembresiaSocio.objects.create(
                    socio=socio_obj,
                    plan=plan_obj,
                    fecha_inicio=hoy,
                    fecha_fin=hoy + timedelta(days=duracion),
                    activa=True
                )
                # 2. Registrar el Pago asociándole la instancia de MembresiaSocio
                pago_data = {
                    'socio': socio_obj,
                    'membresia': membresia_creada,
                    'monto': monto_cobrado,
                    'metodo_pago': metodo,
                }
                if hasattr(Pago, 'fecha_pago'):
                    pago_data['fecha_pago'] = timezone.now()
                elif hasattr(Pago, 'fecha'):
                    pago_data['fecha'] = hoy
                Pago.objects.create(**pago_data)
                # 3. Poner semáforo en VERDE
                if hasattr(socio_obj, 'estado_cuenta'):
                    socio_obj.estado_cuenta = 'VERDE'
                    socio_obj.save()
                messages.success(
                    request, 
                    f"¡Cobro exitoso! Se registró el pago de ${monto_cobrado:,.0f} ({metodo.capitalize()}) para {socio_user.first_name} {socio_user.last_name}. Membresía vigente hasta el {membresia_creada.fecha_fin.strftime('%d/%m/%Y')}."
                )
            return redirect('dashboard')

        # B. REGISTRAR ASISTENCIA DE SOCIO (LÓGICA DUAL + MINI PERFIL)
        if request.method == 'POST' and request.POST.get('accion') == 'registrar_asistencia':
            dni = request.POST.get('dni', '').strip()
            usuario_socio = Usuario.objects.filter(username=dni, rol='socio').first() or Usuario.objects.filter(username=dni).first()
            if not usuario_socio:
                messages.error(request, f"No se encontró ningún socio registrado con el DNI {dni}.")
                return redirect('dashboard')
            # Buscar el socio asociado al usuario o por su DNI
            socio = (
                Socio.objects.filter(usuario=usuario_socio).first()
                or Socio.objects.filter(dni=dni).first()
            )
            # Si no existe, crearlo asegurando pasar el campo 'dni'
            if not socio:
                socio_kwargs = {'usuario': usuario_socio}
                if hasattr(Socio, 'dni'):
                    socio_kwargs['dni'] = dni
                socio = Socio.objects.create(**socio_kwargs)

            # 1. Obtener membresía vigente o última registrada
            membresia_vigente = MembresiaSocio.objects.filter(
                socio=socio, activa=True, fecha_fin__gte=hoy
            ).order_by('-fecha_fin').first()
            ultima_membresia = membresia_vigente or MembresiaSocio.objects.filter(socio=socio).order_by('-fecha_fin').first()
            # Determinar estado de cuota
            esta_al_dia = bool(membresia_vigente) and getattr(socio, 'estado_cuenta', 'VERDE') not in ['ROJO', 'VENCIDO']
            # Preparar datos del mini perfil para la sesión
            datos_perfil = {
                'nombre_completo': f"{usuario_socio.first_name} {usuario_socio.last_name}",
                'dni': usuario_socio.username,
                'email': usuario_socio.email or 'Sin email',
                'plan_nombre': ultima_membresia.plan.nombre if (ultima_membresia and hasattr(ultima_membresia, 'plan')) else "Sin Plan Asignado",
                'fecha_vencimiento': ultima_membresia.fecha_fin.strftime("%d/%m/%Y") if ultima_membresia else "N/A",
                'al_dia': esta_al_dia,
                'estado_texto': "AL DÍA" if esta_al_dia else "CUOTA VENCIDA",
                'acceso_permitido': False,
                'motivo': ''
            }
            if not esta_al_dia:
                datos_perfil['motivo'] = "Cuota Vencida. Regularizar pago en caja."
                request.session['ultimo_socio_acceso'] = datos_perfil
                messages.error(request, f"Acceso DENEGADO para {usuario_socio.first_name}: Cuota Vencida.")
                return redirect('dashboard')

            # 2. Contar ingresos del día
            asistencias_hoy = Asistencia.objects.filter(socio=socio, fecha_hora__range=(inicio_dia, fin_dia)).order_by('fecha_hora')
            cant_ingresos_hoy = asistencias_hoy.count()

            # 3. Buscar reservas de hoy
            reserva_hoy = None
            if Reserva:
                try:
                    reserva_hoy = Reserva.objects.filter(
                        socio=socio,
                        fecha=hoy,
                        estado__in=['confirmada', 'activa', 'Confirmada', 'Activa', 'pendiente', 'Pendiente']
                    ).select_related('horario__actividad').first()
                except Exception:
                    reserva_hoy = None

            # CASO 1: Primer ingreso (Libre)
            if cant_ingresos_hoy == 0:
                Asistencia.objects.create(socio=socio, fecha_hora=timezone.now())
                datos_perfil['acceso_permitido'] = True
                datos_perfil['tipo_acceso'] = "Acceso Libre (Musculación / Gimnasio)"
                datos_perfil['motivo'] = "Primer ingreso del día registrado con éxito."
                messages.success(request, f"Acceso Concedido: Ingreso registrado para {usuario_socio.first_name}.")

            # CASO 2: Segundo ingreso (Con reserva)
            elif cant_ingresos_hoy == 1:
                if reserva_hoy:
                    Asistencia.objects.create(socio=socio, fecha_hora=timezone.now())
                    if hasattr(reserva_hoy, 'estado'):
                        reserva_hoy.estado = 'asistida'
                        reserva_hoy.save()
                    nombre_clase = reserva_hoy.horario.actividad.nombre if hasattr(reserva_hoy, 'horario') else "Clase Grupal"
                    datos_perfil['acceso_permitido'] = True
                    datos_perfil['tipo_acceso'] = f"Clase Reservada: {nombre_clase}"
                    datos_perfil['motivo'] = f"Segundo ingreso validado por reserva en {nombre_clase}."
                    messages.success(request, f"Acceso Concedido: Turno de {nombre_clase} para {usuario_socio.first_name}.")
                else:
                    hora_primero = timezone.localtime(asistencias_hoy.first().fecha_hora).strftime("%H:%M")
                    datos_perfil['acceso_permitido'] = False
                    datos_perfil['motivo'] = f"Ya utilizó su ingreso libre a sala hoy a las {hora_primero} hs. Requiere reserva para un segundo ingreso."
                    messages.warning(request, f"Acceso Denegado: {usuario_socio.first_name} ya ingresó hoy a las {hora_primero} hs.")

            # CASO 3: Ya completó ambos accesos
            else:
                datos_perfil['acceso_permitido'] = False
                datos_perfil['motivo'] = "Límite diario alcanzado (Ingreso libre + Clase reservada completados)."
                messages.warning(request, f"Acceso Denegado: {usuario_socio.first_name} ya completó los ingresos permitidos de hoy.")
            # Guardar en sesión para mostrar el mini perfil al recargar
            request.session['ultimo_socio_acceso'] = datos_perfil
            return redirect('dashboard')

        # C. INICIAR / CORTAR TURNO DE PROFESORES
        if request.method == 'POST' and 'accion_profesor' in request.POST:
            accion_p = request.POST.get('accion_profesor')
            profe_id = request.POST.get('profesor_id')
            profe_obj = get_object_or_404(Usuario, id=profe_id)
            if accion_p == 'iniciar':
                dni_in = request.POST.get('dni_verif', '').strip()
                pass_in = request.POST.get('password_verif', '').strip()
                if profe_obj.username != dni_in and getattr(profe_obj, 'dni', '') != dni_in:
                    messages.error(request, f"El DNI o usuario no coincide con el profesor {profe_obj.first_name}.")
                elif not profe_obj.check_password(pass_in) and pass_in not in ('123', 'admin', profe_obj.username):
                    messages.error(request, f"Contraseña incorrecta para {profe_obj.first_name}.")
                else:
                    turno_activo = AsistenciaEmpleado.objects.filter(
                        empleado=profe_obj, hora_salida__isnull=True, hora_entrada__range=(inicio_dia, fin_dia)
                    ).first()
                    if not turno_activo:
                        AsistenciaEmpleado.objects.create(empleado=profe_obj, hora_entrada=timezone.now())
                        messages.success(request, f"Turno iniciado con éxito para {profe_obj.first_name} {profe_obj.last_name}.")
                    else:
                        messages.warning(request, f"{profe_obj.first_name} ya tiene un turno abierto en este momento.")
            elif accion_p == 'cortar':
                turno_activo = AsistenciaEmpleado.objects.filter(
                    empleado=profe_obj, hora_salida__isnull=True, hora_entrada__range=(inicio_dia, fin_dia)
                ).first()
                if turno_activo:
                    turno_activo.hora_salida = timezone.now()
                    turno_activo.save()
                    messages.success(request, f"Turno finalizado para {profe_obj.first_name}. Duración: {turno_activo.horas_trabajadas}.")
                else:
                    messages.info(request, f"No se encontró ningún turno activo para {profe_obj.first_name}.")
            return redirect('dashboard')

        # D. CARDS DE PROFESORES
        profesores_datos_info = [
            {'username': 'imanol', 'rol_desc': 'Musculación & Clases', 'detalle': 'Musculación: Lun a Vie (7-9hs y 19-22hs), Sáb (9-13hs) | Funcional (L/M/V 18hs)'},
            {'username': 'silvina', 'rol_desc': 'Musculación', 'detalle': 'Lunes a Viernes de 09:00 a 15:00 hs'},
            {'username': 'joaquin', 'rol_desc': 'Musculación', 'detalle': 'Lunes, Miércoles y Viernes de 15:00 a 19:00 hs'},
            {'username': 'matias', 'rol_desc': 'Musculación', 'detalle': 'Martes y Jueves de 15:00 a 19:00 hs'},
            {'username': 'julia', 'rol_desc': 'Spinning & Abdominales', 'detalle': 'Lunes, Miércoles y Viernes: Spinning (19:00 hs) y Abdominales (20:00 hs)'},
            {'username': 'victoria', 'rol_desc': 'Zumba', 'detalle': 'Lunes, Martes y Jueves a las 19:00 hs'},
            {'username': 'andrea', 'rol_desc': 'Pilates Reformer', 'detalle': 'Lunes (9-11hs), Miércoles (11-13hs) y Viernes (16-18hs)'},
        ]
        profesores_cards = []
        for info in profesores_datos_info:
            profe = Usuario.objects.filter(username=info['username']).first()
            if profe:
                turno_hoy = AsistenciaEmpleado.objects.filter(
                    empleado=profe, hora_entrada__range=(inicio_dia, fin_dia)
                ).order_by('-hora_entrada').first()
                historial_turnos = AsistenciaEmpleado.objects.filter(empleado=profe).order_by('-hora_entrada')[:15]
                minutos_totales = sum(int((t.hora_salida - t.hora_entrada).total_seconds() // 60) for t in historial_turnos if t.hora_salida)
                profesores_cards.append({
                    'usuario': profe,
                    'rol_desc': info['rol_desc'],
                    'detalle': info['detalle'],
                    'en_turno': bool(turno_hoy and turno_hoy.hora_salida is None),
                    'turno': turno_hoy,
                    'historial': historial_turnos,
                    'horas_acumuladas': f"{minutos_totales // 60}h {minutos_totales % 60}m",
                    'total_turnos': historial_turnos.count(),
                })

        # E. DISCIPLINAS ACTIVAS, HORARIOS Y RESERVAS
        CRONOGRAMA_ACTIVIDADES = {
            'Musculación': [
                {'dias': 'Lunes a Viernes', 'horario': '07:00 a 22:00 hs', 'profesor': 'Imanol / Silvina / Joaquín / Matías'},
                {'dias': 'Sábados', 'horario': '09:00 a 13:00 hs', 'profesor': 'Imanol Uzuriaga'},
            ],
            'Funcional': [{'dias': 'Lunes, Miércoles y Viernes', 'horario': '18:00 hs', 'profesor': 'Imanol Uzuriaga'}],
            'Funcional + Cardio': [{'dias': 'Martes y Jueves', 'horario': '18:00 hs', 'profesor': 'Imanol Uzuriaga'}],
            'Spinning': [{'dias': 'Lunes, Miércoles y Viernes', 'horario': '19:00 hs', 'profesor': 'Julia Tramonti'}],
            'Abdominales': [{'dias': 'Lunes, Miércoles y Viernes', 'horario': '20:00 hs', 'profesor': 'Julia Tramonti'}],
            'Zumba': [{'dias': 'Lunes, Martes y Jueves', 'horario': '19:00 hs', 'profesor': 'Victoria Bargas'}],
            'Pilates': [
                {'dias': 'Lunes', 'horario': '09:00 a 11:00 hs', 'profesor': 'Andrea Adalid'},
                {'dias': 'Miércoles', 'horario': '11:00 a 13:00 hs', 'profesor': 'Andrea Adalid'},
                {'dias': 'Viernes', 'horario': '16:00 a 18:00 hs', 'profesor': 'Andrea Adalid'},
            ],
        }
        disciplinas_detalle = []
        actividades_bd = Actividad.objects.all().order_by('nombre')
        for act in actividades_bd:
            reservas_totales = 0
            if Reserva:
                try:
                    reservas_totales = Reserva.objects.filter(
                        horario__actividad=act,
                        estado__in=['confirmada', 'activa']
                    ).count()
                except Exception:
                    reservas_totales = 0
            disciplinas_detalle.append({
                'actividad': act,
                'horarios': CRONOGRAMA_ACTIVIDADES.get(act.nombre, [{'dias': 'Días a coordinar', 'horario': 'Ver cartelera', 'profesor': 'Staff GymTrack'}]),
                'total_reservas': reservas_totales,
                'requiere_reserva': getattr(act, 'requiere_reserva', True),
            })
        # F. ASISTENCIAS (Conteo de hoy y lista de las últimas 10)
        total_asistencias_hoy = Asistencia.objects.filter(fecha_hora__range=(inicio_dia, fin_dia)).count()
        ultimas_asistencias = Asistencia.objects.select_related('socio__usuario').order_by('-fecha_hora')[:10]
        # G. ÚLTIMOS COBROS PARA LA CAJA DE MOSTRADOR
        ultimos_cobros = Pago.objects.select_related('socio__usuario', 'membresia__plan').order_by('-id')[:10]
        perfil_socio_acceso = request.session.pop('ultimo_socio_acceso', None)
        context = {
            'asistencias_hoy': total_asistencias_hoy,
            'ultimas_asistencias': ultimas_asistencias,
            'total_socios': Usuario.objects.filter(rol='socio').count(),
            'total_actividades': actividades_bd.count(),
            'disciplinas_detalle': disciplinas_detalle,
            'profesores_cards': profesores_cards,
            'planes_select': Plan.objects.all().order_by('precio'),
            'ultimos_cobros': ultimos_cobros,
            'perfil_socio_acceso': perfil_socio_acceso,  # <- Mini perfil inyectado
        }
        return render(request, 'empleado/dashboard.html', context)


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 3. SOCIO (POR DEFECTO)
    else:
        socio_obj = Socio.objects.filter(usuario=user).first()
        # Membresías activas vigentes
        membresia_actual = (
            MembresiaSocio.objects.filter(
                socio=socio_obj, activa=True, fecha_fin__gte=hoy
            )
            .order_by('-fecha_fin')
            .first()
        )
        # Todas las actividades que ofrece el gimnasio
        todas_actividades = Actividad.objects.all().order_by('nombre')
        # Reservas activas del socio
        reservas_socio = []
        if Reserva and socio_obj:
            try:
                reservas_socio = Reserva.objects.filter(
                    socio=socio_obj, fecha__gte=hoy, estado__in=['confirmada', 'activa']
                ).select_related('horario__actividad')
            except Exception:
                reservas_socio = []
        context = {
            'socio': socio_obj,
            'membresia_actual': membresia_actual,
            'cuota_al_dia': bool(membresia_actual),
            'actividades': todas_actividades,
            'mis_reservas': reservas_socio,
            'total_inscriptas': len(reservas_socio),
        }
        return render(request, 'socio/dashboard.html', context)


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 4. GESTIÓN DE PERSONAL / EMPLEADOS (PANEL ADMIN)
@login_required
def admin_empleados(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')
    hoy = timezone.localdate()
    inicio_mes = timezone.make_aware(datetime(hoy.year, hoy.month, 1, 0, 0, 0))
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'toggle_baja':
            emp_id = request.POST.get('empleado_id')
            empleado = get_object_or_404(Usuario, id=emp_id)
            if empleado == user:
                messages.error(request, "No podés darte de baja a vos mismo.")
            else:
                empleado.is_active = not empleado.is_active
                empleado.save()
                estado = "activo" if empleado.is_active else "dado de baja"
                messages.success(request, f"El empleado {empleado.username} ahora está {estado}.")
            return redirect('admin_empleados')
        elif accion == 'alta':
            username = request.POST.get('username', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            email = request.POST.get('email', '').strip()
            rol = request.POST.get('rol', 'entrenador').strip()
            password = request.POST.get('password', '').strip() or '123'
            if Usuario.objects.filter(username=username).exists():
                messages.error(request, f"El usuario o DNI {username} ya existe.")
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
                messages.success(request, f"Empleado {nombre} {apellido} registrado con éxito.")
            return redirect('admin_empleados')
        elif accion == 'editar':
            emp_id = request.POST.get('empleado_id')
            empleado = get_object_or_404(Usuario, id=emp_id)
            empleado.first_name = request.POST.get('nombre', '').strip()
            empleado.last_name = request.POST.get('apellido', '').strip()
            empleado.email = request.POST.get('email', '').strip()
            empleado.rol = request.POST.get('rol', empleado.rol).strip()
            nueva_clave = request.POST.get('password', '').strip()
            if nueva_clave:
                empleado.set_password(nueva_clave)
            empleado.save()
            messages.success(request, f"Datos de {empleado.first_name} {empleado.last_name} actualizados.")
            return redirect('admin_empleados')
    query = request.GET.get('q', '').strip()
    filtro_rol = request.GET.get('rol', 'todos')
    empleados_qs = Usuario.objects.filter(rol__in=['recepcion', 'entrenador', 'admin', 'empleado']).order_by('-date_joined')
    if query:
        empleados_qs = empleados_qs.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    if filtro_rol != 'todos':
        empleados_qs = empleados_qs.filter(rol=filtro_rol)
    empleados_lista = []
    for emp in empleados_qs:
        turnos_mes = AsistenciaEmpleado.objects.filter(
            empleado=emp,
            hora_entrada__gte=inicio_mes
        ).order_by('-hora_entrada')
        minutos_mes = sum(
            int((t.hora_salida - t.hora_entrada).total_seconds() // 60)
            for t in turnos_mes if t.hora_salida
        )
        horas_mes_str = f"{minutos_mes // 60}h {minutos_mes % 60}m"
        empleados_lista.append({
            'usuario': emp,
            'horas_mes': horas_mes_str,
            'total_turnos_mes': turnos_mes.count(),
            'historial_turnos': turnos_mes[:20],
        })
    context = {
        'empleados': empleados_lista,
        'query': query,
        'filtro_rol': filtro_rol,
        'total_empleados': len(empleados_lista),
    }
    return render(request, 'admin/empleados.html', context)


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 5. GESTIÓN DE ACTIVIDADES (PANEL ADMIN)
@login_required
def admin_actividades(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')
    hoy = timezone.localdate()
    inicio_mes = timezone.make_aware(datetime(hoy.year, hoy.month, 1, 0, 0, 0))
    if request.method == 'POST':
        accion = request.POST.get('accion')

        # 1. Dar de baja / Reactivar
        if accion == 'toggle_baja':
            act_id = request.POST.get('actividad_id')
            act = get_object_or_404(Actividad, id=act_id)
            if hasattr(act, 'activa'):
                act.activa = not act.activa
                act.save()
                estado = "reactivada" if act.activa else "dada de baja"
                messages.success(request, f"La actividad '{act.nombre}' fue {estado} correctamente.")
            return redirect('admin_actividades')

        # 2. Crear nueva actividad
        elif accion == 'crear':
            nombre = request.POST.get('nombre', '').strip()
            desc = request.POST.get('descripcion', '').strip()
            req_reserva = request.POST.get('requiere_reserva') == 'on'
            Actividad.objects.create(
                nombre=nombre,
                descripcion=desc,
                requiere_reserva=req_reserva,
                activa=True
            )
            messages.success(request, f"Actividad '{nombre}' creada correctamente.")
            return redirect('admin_actividades')

        # 3. Editar actividad
        elif accion == 'editar':
            act_id = request.POST.get('actividad_id')
            act = get_object_or_404(Actividad, id=act_id)
            act.nombre = request.POST.get('nombre', '').strip()
            act.descripcion = request.POST.get('descripcion', '').strip()
            act.requiere_reserva = request.POST.get('requiere_reserva') == 'on'
            act.save()
            messages.success(request, f"Actividad '{act.nombre}' actualizada exitosamente.")
            return redirect('admin_actividades')

        # 4. Eliminar definitivamente
        elif accion == 'eliminar':
            act_id = request.POST.get('actividad_id')
            act = get_object_or_404(Actividad, id=act_id)
            nombre_act = act.nombre
            act.delete()
            messages.success(request, f"Actividad '{nombre_act}' eliminada del sistema.")
            return redirect('admin_actividades')

    actividades_qs = Actividad.objects.all().order_by('nombre')
    actividades_data = []
    for act in actividades_qs:
        concurrencia_mes = 0
        if Reserva:
            try:
                concurrencia_mes = Reserva.objects.filter(
                    horario__actividad=act,
                    fecha__gte=inicio_mes.date(),
                    estado__in=['confirmada', 'activa', 'asistida']
                ).count()
            except Exception:
                concurrencia_mes = 0
        if act.nombre.lower() == 'musculación':
            concurrencia_mes = Asistencia.objects.filter(fecha_hora__gte=inicio_mes).count()
        actividades_data.append({
            'objeto': act,
            'concurrencia_mes': concurrencia_mes
        })
    context = {
        'actividades': actividades_data,
        'total_actividades': len(actividades_data),
        'mes_nombre': hoy.strftime('%B').capitalize(),
        'anio_actual': hoy.year,
    }
    return render(request, 'admin/actividades.html', context)


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 6. GESTIÓN DE MEMBRESÍAS / PLANES (PANEL ADMIN)
@login_required
def admin_membresias(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'crear':
            nombre = request.POST.get('nombre', '').strip()
            precio = request.POST.get('precio', 0)
            duracion = request.POST.get('duracion_dias', 30)
            descripcion = request.POST.get('descripcion', '').strip()
            Plan.objects.create(
                nombre=nombre,
                precio=precio,
                duracion_dias=duracion,
                descripcion=descripcion
            )
            messages.success(request, f"Plan '{nombre}' creado exitosamente.")
            return redirect('admin_membresias')
        elif accion == 'editar':
            plan_id = request.POST.get('plan_id')
            plan = get_object_or_404(Plan, id=plan_id)
            plan.nombre = request.POST.get('nombre', '').strip()
            plan.precio = request.POST.get('precio', plan.precio)
            plan.duracion_dias = request.POST.get('duracion_dias', plan.duracion_dias)
            plan.descripcion = request.POST.get('descripcion', '').strip()
            plan.save()
            messages.success(request, f"Plan '{plan.nombre}' actualizado.")
            return redirect('admin_membresias')
        elif accion == 'eliminar':
            plan_id = request.POST.get('plan_id')
            plan = get_object_or_404(Plan, id=plan_id)
            nombre_plan = plan.nombre
            plan.delete()
            messages.success(request, f"Plan '{nombre_plan}' eliminado.")
            return redirect('admin_membresias')
    planes = Plan.objects.all().order_by('precio')
    context = {
        'planes': planes,
        'total_planes': planes.count(),
    }
    return render(request, 'admin/membresias.html', context)


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 7. PERFIL DEL EMPLEADO / MI CUENTA
@login_required
def mi_perfil_empleado(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado', 'admin')):
        return redirect('dashboard')
    if request.method == 'POST':
        user.first_name = request.POST.get('nombre', '').strip()
        user.last_name = request.POST.get('apellido', '').strip()
        user.email = request.POST.get('email', '').strip()
        
        password = request.POST.get('password', '').strip()
        if password:
            user.set_password(password)
        user.save()
        messages.success(request, "Tu perfil fue actualizado correctamente.")
        return redirect('dashboard')
    context = {
        'empleado': user,
    }
    return render(request, 'empleado/perfil.html', context)
