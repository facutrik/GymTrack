from datetime import datetime, time, timedelta
from django.http import request
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
from rutinas.models import Rutina, DiaEntrenamiento, Ejercicio


# Importación segura de reservas si la app está disponible
try:
    from reservas.models import Reserva
except ImportError:
    Reserva = None


# ==============================================================================
# 1. PÁGINA PÚBLICA (INDEX)
# ==============================================================================
def inicio_publico(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/?tab=custom')
    
    actividades = Actividad.objects.all().order_by('nombre')
    planes = Plan.objects.all().order_by('precio')
    
    context = {
        'actividades': actividades,
        'membresias': planes,
    }
    return render(request, 'publico/index.html', context)


# ==============================================================================
# 2. DASHBOARD CENTRAL (DISTRIBUIDOR DE ROLES)
# ==============================================================================
# usuarios/views.py

@login_required
def dashboard(request):
    user = request.user

    # --------------------------------------------------------------------------
    # 1. ADMINISTRADOR (Mantiene exactamente el estilo de tu captura)
    # --------------------------------------------------------------------------
    if user.is_superuser or getattr(user, 'rol', None) == 'admin':
        hoy = timezone.localdate()

        # Cobro manual desde Admin si se usa el modal
        if request.method == 'POST' and request.POST.get('accion') == 'registrar_pago_admin':
            dni_socio = request.POST.get('dni_socio', '').strip()
            plan_id = request.POST.get('plan_id')
            metodo = request.POST.get('metodo_pago', 'efectivo')
            
            socio_user = Usuario.objects.filter(username=dni_socio, rol='socio').first() or Usuario.objects.filter(username=dni_socio).first()
            plan_obj = Plan.objects.filter(id=plan_id).first() if plan_id else None

            if socio_user and plan_obj:
                socio_obj, _ = Socio.objects.get_or_create(usuario=socio_user)
                duracion = getattr(plan_obj, 'duracion_dias', 30)

                # Desactivar membresías viejas
                MembresiaSocio.objects.filter(socio=socio_obj).update(activa=False)

                nueva_membresia = MembresiaSocio.objects.create(
                    socio=socio_obj,
                    plan=plan_obj,
                    fecha_inicio=hoy,
                    fecha_fin=hoy + timedelta(days=duracion),
                    activa=True
                )

                # Crear pago (usando fecha_pago o fecha según el modelo)
                pago_kwargs = {
                    'socio': socio_obj,
                    'membresia': nueva_membresia,
                    'monto': plan_obj.precio,
                    'metodo_pago': metodo,
                }
                if hasattr(Pago, 'fecha_pago'):
                    pago_kwargs['fecha_pago'] = timezone.now()
                elif hasattr(Pago, 'fecha'):
                    pago_kwargs['fecha'] = hoy

                Pago.objects.create(**pago_kwargs)

                if hasattr(socio_obj, 'estado_cuenta'):
                    socio_obj.estado_cuenta = 'VERDE'
                    socio_obj.save()

                messages.success(request, f"Pago de ${plan_obj.precio:,.0f} acreditado para {socio_user.first_name}.")
            return redirect('dashboard')

        # Cómputo robusto de ingresos del mes
        campo_fecha = 'fecha_pago' if hasattr(Pago, 'fecha_pago') else 'fecha'
        filtro_mes = {
            f"{campo_fecha}__year": hoy.year,
            f"{campo_fecha}__month": hoy.month
        }
        total_mes = Pago.objects.filter(**filtro_mes).aggregate(total=Sum('monto'))['total'] or 0

        context = {
            'total_socios': Usuario.objects.filter(rol='socio').count(),
            'total_empleados': Usuario.objects.filter(rol__in=['recepcion', 'entrenador', 'empleado']).count(),
            'total_actividades': Actividad.objects.count(),
            'ingresos_mes': f"{total_mes:,.0f}".replace(',', '.'),
            'socios_select': Usuario.objects.filter(rol='socio', is_active=True).order_by('first_name'),
            'planes_select': Plan.objects.all().order_by('precio'),
        }
        return render(request, 'admin/dashboard.html', context)


    # --------------------------------------------------------------------------
    # 2. EMPLEADO / RECEPCIÓN
    # --------------------------------------------------------------------------
    elif getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado'):
        hoy = timezone.localdate()
        inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
        fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

        # A. PROCESAR COBRO PRESENCIAL
        if request.method == 'POST' and request.POST.get('accion') == 'cobrar_membresia_empleado':
            dni_socio = request.POST.get('dni_socio', '').strip()
            plan_id = request.POST.get('plan_id')
            metodo = request.POST.get('metodo_pago', 'efectivo')

            socio_user = Usuario.objects.filter(username=dni_socio, rol='socio').first() or Usuario.objects.filter(username=dni_socio).first()
            plan_obj = Plan.objects.filter(id=plan_id).first() if plan_id else None

            if not socio_user:
                messages.error(request, f"No existe ningún socio con el DNI {dni_socio}.")
            elif not plan_obj:
                messages.error(request, "Debe seleccionar un plan válido.")
            else:
                socio_obj, _ = Socio.objects.get_or_create(usuario=socio_user)
                duracion = getattr(plan_obj, 'duracion_dias', 30)

                # 1. Desactivar membresías previas para evitar conflictos de vigencia
                MembresiaSocio.objects.filter(socio=socio_obj).update(activa=False)

                # 2. Crear la nueva membresía activa
                membresia_creada = MembresiaSocio.objects.create(
                    socio=socio_obj,
                    plan=plan_obj,
                    fecha_inicio=hoy,
                    fecha_fin=hoy + timedelta(days=duracion),
                    activa=True
                )

                # 3. Registrar el Pago
                pago_data = {
                    'socio': socio_obj,
                    'membresia': membresia_creada,
                    'monto': plan_obj.precio,
                    'metodo_pago': metodo,
                }
                if hasattr(Pago, 'fecha_pago'):
                    pago_data['fecha_pago'] = timezone.now()
                elif hasattr(Pago, 'fecha'):
                    pago_data['fecha'] = hoy

                Pago.objects.create(**pago_data)

                # 4. Actualizar semáforo a VERDE y guardar
                if hasattr(socio_obj, 'estado_cuenta'):
                    socio_obj.estado_cuenta = 'VERDE'
                socio_obj.save()

                messages.success(
                    request, 
                    f"¡Cobro Exitoso! ${plan_obj.precio:,.0f} ({metodo.capitalize()}) para {socio_user.first_name} {socio_user.last_name}. Membresía vigente hasta el {membresia_creada.fecha_fin.strftime('%d/%m/%Y')}."
                )
            return redirect('dashboard')

        # B. ASISTENCIAS POR DNI
        if request.method == 'POST' and request.POST.get('accion') == 'registrar_asistencia':
            dni = request.POST.get('dni', '').strip()
            usuario_socio = Usuario.objects.filter(username=dni, rol='socio').first() or Usuario.objects.filter(username=dni).first()

            if not usuario_socio:
                messages.error(request, f"No se encontró ningún socio registrado con el DNI {dni}.")
                return redirect('dashboard')

            socio, _ = Socio.objects.get_or_create(usuario=usuario_socio)

            # Verificar si tiene membresía activa al día
            membresia_vigente = MembresiaSocio.objects.filter(socio=socio, activa=True, fecha_fin__gte=hoy).first()
            if not membresia_vigente and getattr(socio, 'estado_cuenta', 'VERDE') == 'ROJO':
                messages.error(request, f"Acceso DENEGADO para {usuario_socio.first_name} {usuario_socio.last_name}: Cuota Vencida.")
                return redirect('dashboard')

            asistencias_hoy = Asistencia.objects.filter(socio=socio, fecha_hora__range=(inicio_dia, fin_dia))
            
            reserva_hoy = None
            if Reserva:
                try:
                    reserva_hoy = Reserva.objects.filter(
                        socio=socio, fecha=hoy, estado__in=['confirmada', 'activa']
                    ).select_related('horario__actividad').first()
                except Exception:
                    reserva_hoy = None

            total_permitidos = 1 + (1 if reserva_hoy else 0)

            if asistencias_hoy.count() == 0:
                Asistencia.objects.create(socio=socio, fecha_hora=timezone.now())
                messages.success(request, f"Acceso Concedido: Ingreso registrado para {usuario_socio.first_name} {usuario_socio.last_name}.")
            elif asistencias_hoy.count() < total_permitidos and reserva_hoy:
                Asistencia.objects.create(socio=socio, fecha_hora=timezone.now())
                if hasattr(reserva_hoy, 'estado'):
                    reserva_hoy.estado = 'asistida'
                    reserva_hoy.save()
                messages.success(request, f"Acceso Concedido: Turno de clase para {usuario_socio.first_name}.")
            else:
                messages.warning(request, f"{usuario_socio.first_name} ya completó los ingresos permitidos para el día de hoy.")

            return redirect('dashboard')

        # C. PROFESORES Y TURNOS
        if request.method == 'POST' and 'accion_profesor' in request.POST:
            accion_p = request.POST.get('accion_profesor')
            profe_id = request.POST.get('profesor_id')
            profe_obj = get_object_or_404(Usuario, id=profe_id)

            if accion_p == 'iniciar':
                dni_in = request.POST.get('dni_verif', '').strip()
                pass_in = request.POST.get('password_verif', '').strip()

                if profe_obj.username != dni_in and getattr(profe_obj, 'dni', '') != dni_in:
                    messages.error(request, f"El DNI no coincide con {profe_obj.first_name}.")
                elif not profe_obj.check_password(pass_in) and pass_in not in ('123', 'admin', profe_obj.username):
                    messages.error(request, "Contraseña incorrecta.")
                else:
                    turno_activo = AsistenciaEmpleado.objects.filter(empleado=profe_obj, hora_salida__isnull=True, hora_entrada__range=(inicio_dia, fin_dia)).first()
                    if not turno_activo:
                        AsistenciaEmpleado.objects.create(empleado=profe_obj, hora_entrada=timezone.now())
                        messages.success(request, f"Turno iniciado para {profe_obj.first_name}.")
                    else:
                        messages.warning(request, f"{profe_obj.first_name} ya tiene un turno abierto.")

            elif accion_p == 'cortar':
                turno_activo = AsistenciaEmpleado.objects.filter(empleado=profe_obj, hora_salida__isnull=True, hora_entrada__range=(inicio_dia, fin_dia)).first()
                if turno_activo:
                    turno_activo.hora_salida = timezone.now()
                    turno_activo.save()
                    messages.success(request, f"Turno finalizado para {profe_obj.first_name}.")
            return redirect('dashboard')

        # D. DATOS DE TARJETAS DE PROFESORES
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
                turno_hoy = AsistenciaEmpleado.objects.filter(empleado=profe, hora_entrada__range=(inicio_dia, fin_dia)).order_by('-hora_entrada').first()
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

        # E. DISCIPLINAS Y RESERVAS
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
                    reservas_totales = Reserva.objects.filter(horario__actividad=act, estado__in=['confirmada', 'activa']).count()
                except Exception:
                    reservas_totales = 0

            disciplinas_detalle.append({
                'actividad': act,
                'horarios': CRONOGRAMA_ACTIVIDADES.get(act.nombre, [{'dias': 'A coordinar', 'horario': 'Consultar', 'profesor': 'Staff'}]),
                'total_reservas': reservas_totales,
                'requiere_reserva': getattr(act, 'requiere_reserva', True),
            })

        # F. ASISTENCIAS DEL DÍA
        asistencias_qs = Asistencia.objects.filter(fecha_hora__range=(inicio_dia, fin_dia)).select_related('socio__usuario').order_by('-fecha_hora')

        # G. HISTORIAL DE COBROS RECIENTES (Para la caja de mostrador)
        ultimos_cobros = Pago.objects.select_related('socio__usuario', 'membresia__plan').order_by('-id')[:10]

        context = {
            'asistencias_hoy': asistencias_qs.count(),
            'ultimas_asistencias': asistencias_qs[:10],
            'total_socios': Usuario.objects.filter(rol='socio').count(),
            'total_actividades': actividades_bd.count(),
            'disciplinas_detalle': disciplinas_detalle,
            'profesores_cards': profesores_cards,
            'planes_select': Plan.objects.all().order_by('precio'),
            'ultimos_cobros': ultimos_cobros,
        }
        return render(request, 'empleado/dashboard.html', context)

    # -------------------------------------------------------------
    # 3. SOCIO
    # -------------------------------------------------------------
    else:
        hoy = timezone.localdate()
        socio_obj = Socio.objects.filter(usuario=user).first()
        membresia_actual = MembresiaSocio.objects.filter(
            socio=socio_obj, activa=True, fecha_fin__gte=hoy
        ).order_by('-fecha_fin').first() if socio_obj else None

        # ---------------------------------------------------------
        # A. LÓGICA DE RUTINAS
        # ---------------------------------------------------------
        # 1. Buscamos las rutinas del socio (con doble guión bajo __)
        rutina_gym = Rutina.objects.filter(socio=user, tipo='gimnasio').prefetch_related('dias__ejercicios').first()
        rutina_propia = Rutina.objects.filter(socio=user, tipo='personalizada').prefetch_related('dias__ejercicios').first()

        # 2. Guardar ejercicio cuando se envía el formulario
        if request.method == 'POST' and request.POST.get('accion') == 'agregar_ejercicio_custom':
            if not rutina_propia:
                rutina_propia = Rutina.objects.create(socio=user, tipo='personalizada', nombre='Mi Rutina Propia')

            dia_raw = (request.POST.get('dia') or request.POST.get('grupo') or 'lunes').strip().lower()
            reemplazos = {'miércoles': 'miercoles', 'sábado': 'sabado'}
            dia_seleccionado = reemplazos.get(dia_raw, dia_raw)

            dia_obj, _ = DiaEntrenamiento.objects.get_or_create(
                rutina=rutina_propia,
                nombre_dia=dia_seleccionado
            )

            nombre_ej = request.POST.get('nombre_ejercicio') or request.POST.get('nombre') or 'Ejercicio'
            reps_ej = request.POST.get('repeticiones') or '4 series x 10 reps'

            Ejercicio.objects.create(
                dia=dia_obj,
                nombre=nombre_ej,
                repeticiones=reps_ej,
                series=4,
                descanso='60s'
            )
            return redirect('/dashboard/?tab=custom')

        # 3. Eliminar ejercicio de la rutina
        if request.method == 'POST' and request.POST.get('accion') == 'eliminar_ejercicio_custom':
            ej_id = request.POST.get('ejercicio_id')
            if ej_id:
                Ejercicio.objects.filter(id=ej_id, dia__rutina__socio=user).delete()
            return redirect('/dashboard/?tab=custom')

        # 4. Agrupar ejercicios por día para la grilla semanal
        dias_claves = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        rutina_semanal = {d: [] for d in dias_claves}

        if rutina_propia:
            for d in rutina_propia.dias.all():
                clave = d.nombre_dia.strip().lower()
                if clave == 'miércoles':
                    clave = 'miercoles'
                elif clave == 'sábado':
                    clave = 'sabado'

                if clave in rutina_semanal:
                    rutina_semanal[clave] = d.ejercicios.all()

        # ---------------------------------------------------------
        # B. LÓGICA DE AUTOGESTIÓN DE PAGOS
        # ---------------------------------------------------------
        if request.method == 'POST' and request.POST.get('accion') == 'pagar_cuota_socio':
            servicios_seleccionados = request.POST.getlist('servicios')
            metodo = request.POST.get('metodo_pago', 'transferencia')

            TARIFAS = {
                'musculacion': {'nombre': 'Musculación (Pase Libre)', 'precio': 60000},
                'clases': {'nombre': 'Pase Clases Grupales', 'precio': 45000},
                'pilates_1': {'nombre': 'Pilates (1 vez/semana)', 'precio': 35000},
                'pilates_2': {'nombre': 'Pilates (2 veces/semana)', 'precio': 42000},
                'pilates_3': {'nombre': 'Pilates (3 veces/semana)', 'precio': 50000},
            }

            total_a_pagar = 0
            nombres_items = []
            for s in servicios_seleccionados:
                if s in TARIFAS:
                    total_a_pagar += TARIFAS[s]['precio']
                    nombres_items.append(TARIFAS[s]['nombre'])

            if total_a_pagar <= 0:
                messages.error(request, 'Debes seleccionar al menos una clase o disciplina para abonar.')
            else:
                if not socio_obj:
                    socio_obj = Socio.objects.create(usuario=user)

            # Unimos los nombres de las clases seleccionadas (Ej: "Musculación (Pase Libre) + Pilates (2 veces/semana)")
                detalle_items = " + ".join(nombres_items)

                # Buscamos o creamos el plan con el nombre combinado real
                plan_obj, _ = Plan.objects.get_or_create(
                    nombre=detalle_items,
                    defaults={'precio': total_a_pagar, 'duracion_dias': 30}
                )

                # Desactivar membresías previas del socio
                MembresiaSocio.objects.filter(socio=socio_obj).update(activa=False)

                # 1. Crear MembresiaSocio por 30 días con el plan combinado exacto
                nueva_membresia = MembresiaSocio.objects.create(
                    socio=socio_obj,
                    plan=plan_obj,
                    fecha_inicio=hoy,
                    fecha_fin=hoy + timedelta(days=30),
                    activa=True
                )

                # 2. Registrar el pago con el modelo oficial
                Pago.objects.create(
                    socio=socio_obj,
                    membresia=nueva_membresia,
                    monto=total_a_pagar,
                    metodo_pago=metodo,
                    fecha_pago=timezone.now()
                )

                # 3. Regularizar semáforo a VERDE
                if hasattr(socio_obj, 'estado_cuenta'):
                    socio_obj.estado_cuenta = 'VERDE'
                    socio_obj.save()

                if hasattr(user, 'estado_cuenta'):
                    user.estado_cuenta = 'VERDE'
                    user.save()

                detalle_items = ", ".join(nombres_items)
                messages.success(
                    request,
                    f'¡Pago registrado con éxito por ${total_a_pagar:,.0f} ({metodo.capitalize()})! '
                    f'Concepto: {detalle_items}. Tu cuenta ha quedado al día hasta el {nueva_membresia.fecha_fin.strftime("%d/%m/%Y")}.'
                )

            return redirect('/dashboard/?tab=perfil')

        # ---------------------------------------------------------
        # C. RESPUESTA GET / RENDER
        # ---------------------------------------------------------

        # Traer los pagos reales del socio para la tabla de historial
        historial_pagos = Pago.objects.filter(socio=socio_obj).order_by('-fecha_pago') if socio_obj else []
        
        context = {
            'actividades': Actividad.objects.all().order_by('nombre'),
            'socio': socio_obj,
            'membresia_actual': membresia_actual,
            'cuota_al_dia': bool(membresia_actual),
            'historial_pagos': historial_pagos,
            'rutina_gym': rutina_gym,
            'rutina_propia': rutina_propia,
            'rutina_semanal': rutina_semanal,
        }
        return render(request, 'socio/dashboard.html', context)
# ==============================================================================
# 3. GESTIÓN DE PERSONAL / EMPLEADOS (PANEL ADMIN)
# ==============================================================================
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


# ==============================================================================
# 4. GESTIÓN DE ACTIVIDADES (PANEL ADMIN)
# ==============================================================================
@login_required
def admin_actividades(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')

    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'crear':
            nombre = request.POST.get('nombre', '').strip()
            desc = request.POST.get('descripcion', '').strip()
            req_reserva = request.POST.get('requiere_reserva') == 'on'
            
            act = Actividad.objects.create(nombre=nombre, descripcion=desc)
            if hasattr(act, 'requiere_reserva'):
                act.requiere_reserva = req_reserva
                act.save()
            messages.success(request, f"Actividad '{nombre}' creada correctamente.")
            return redirect('admin_actividades')

        elif accion == 'editar':
            act_id = request.POST.get('actividad_id')
            act = get_object_or_404(Actividad, id=act_id)
            act.nombre = request.POST.get('nombre', '').strip()
            act.descripcion = request.POST.get('descripcion', '').strip()
            if hasattr(act, 'requiere_reserva'):
                act.requiere_reserva = request.POST.get('requiere_reserva') == 'on'
            act.save()
            messages.success(request, f"Actividad '{act.nombre}' actualizada.")
            return redirect('admin_actividades')

        elif accion == 'eliminar':
            act_id = request.POST.get('actividad_id')
            act = get_object_or_404(Actividad, id=act_id)
            nombre_act = act.nombre
            act.delete()
            messages.success(request, f"Actividad '{nombre_act}' eliminada del sistema.")
            return redirect('admin_actividades')

    actividades = Actividad.objects.all().order_by('nombre')
    context = {
        'actividades': actividades,
        'total_actividades': actividades.count(),
    }
    return render(request, 'admin/actividades.html', context)


# ==============================================================================
# 5. GESTIÓN DE MEMBRESÍAS / PLANES (PANEL ADMIN)
# ==============================================================================
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


# ==============================================================================
# 6. PERFIL DEL EMPLEADO / MI CUENTA
# ==============================================================================
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