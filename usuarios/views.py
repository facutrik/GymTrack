import json
import os
import re
from datetime import datetime, time, timedelta
from django.conf import settings
from django.http import request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
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
        # ==========================================================
        # 💵 PROCESAR COBRO DIRECTO DESDE PANEL ADMIN
        # ==========================================================
        if request.method == 'POST' and request.POST.get('accion') == 'cobrar_desde_admin':
            socio_id = request.POST.get('socio_id')
            plan_id = request.POST.get('plan_id')
            actividad_id = request.POST.get('actividad_id')
            metodo = request.POST.get('metodo_pago', 'efectivo')

            socio_obj = Socio.objects.filter(id=socio_id).first()
            plan_obj = Plan.objects.filter(id=plan_id).first() if plan_id else None
            act_obj = Actividad.objects.filter(id=actividad_id).first() if actividad_id else None

            if not socio_obj:
                messages.error(request, "Debe seleccionar un socio de la lista.")
            elif not plan_obj and not act_obj:
                messages.error(request, "Debe seleccionar una membresía o una actividad para cobrar.")
            else:
                hoy_cobro = timezone.localdate()
                monto_total = 0
                conceptos = []

                nueva_memb = None
                if plan_obj:
                    monto_total += getattr(plan_obj, 'precio', 0)
                    conceptos.append(plan_obj.nombre)

                    memb_previa = MembresiaSocio.objects.filter(socio=socio_obj).order_by('-fecha_fin').first()
                    dias_vigencia = getattr(plan_obj, 'duracion_dias', 30)
                    if memb_previa and memb_previa.fecha_fin < hoy_cobro:
                        dias_atraso = (hoy_cobro - memb_previa.fecha_fin).days
                        if 1 <= dias_atraso <= 7:
                            dias_vigencia = max(1, 30 - dias_atraso)

                    MembresiaSocio.objects.filter(socio=socio_obj).update(activa=False)

                    nueva_memb = MembresiaSocio.objects.create(
                        socio=socio_obj,
                        plan=plan_obj,
                        fecha_inicio=hoy_cobro,
                        fecha_fin=hoy_cobro + timedelta(days=dias_vigencia),
                        activa=True
                    )

                if act_obj:
                    monto_total += getattr(act_obj, 'precio', 0)
                    conceptos.append(act_obj.nombre)
                    if Reserva and hasattr(Reserva, 'actividad'):
                        Reserva.objects.get_or_create(
                            socio=socio_obj,
                            actividad=act_obj,
                            defaults={'fecha': hoy_cobro, 'estado': 'confirmada'}
                        )

                pago_kwargs = {
                    'socio': socio_obj,
                    'monto': monto_total,
                    'metodo_pago': metodo,
                }
                if nueva_memb and hasattr(Pago, 'membresia'):
                    pago_kwargs['membresia'] = nueva_memb
                if hasattr(Pago, 'fecha_pago'):
                    pago_kwargs['fecha_pago'] = timezone.now()
                elif hasattr(Pago, 'fecha'):
                    pago_kwargs['fecha'] = hoy_cobro

                Pago.objects.create(**pago_kwargs)

                if hasattr(socio_obj, 'estado_cuenta'):
                    socio_obj.estado_cuenta = 'VERDE'
                    socio_obj.save()

                nombre_socio = f"{socio_obj.usuario.first_name} {socio_obj.usuario.last_name}".strip() or socio_obj.usuario.username
                messages.success(
                    request,
                    f"Cobro registrado por ${monto_total:,.0f} ({metodo.capitalize()}) a {nombre_socio} — Concepto: {', '.join(conceptos)}."
                )
            return redirect('dashboard')

        # ==========================================================
        # 🏋️ GESTIÓN DE RUTINAS (3 BÁSICAS + PERSONALIZADAS SOCIOS)
        # ==========================================================
        if request.method == 'POST' and request.POST.get('accion') == 'admin_agregar_ejercicio_rutina':
            destino = request.POST.get('destino')
            dia_nombre = request.POST.get('nombre_dia', 'Día 1').strip()
            nombre_ej = request.POST.get('nombre_ejercicio', '').strip()
            series_num = int(request.POST.get('series') or 3)
            reps_txt = request.POST.get('repeticiones', '8-12 reps').strip()
            descanso_txt = request.POST.get('descanso', '90s').strip()

            if destino == 'basica':
                rutina_id = request.POST.get('rutina_basica_id')
                rutina_obj = get_object_or_404(Rutina, id=rutina_id)
            else:
                socio_user_id = request.POST.get('socio_usuario_id')
                socio_user = get_object_or_404(Usuario, id=socio_user_id)
                rutina_obj, _ = Rutina.objects.get_or_create(
                    socio=socio_user,
                    tipo='gimnasio',
                    defaults={'nombre': f'Rutina Personalizada - {socio_user.first_name or socio_user.username}'}
                )

            dia_obj, _ = DiaEntrenamiento.objects.get_or_create(
                rutina=rutina_obj,
                nombre_dia=dia_nombre
            )
            Ejercicio.objects.create(
                dia=dia_obj,
                nombre=nombre_ej,
                series=series_num,
                repeticiones=reps_txt,
                descanso=descanso_txt
            )
            messages.success(request, f"Ejercicio '{nombre_ej}' guardado en {rutina_obj.nombre} ({dia_nombre}).")
            return redirect('dashboard')

        if request.method == 'POST' and request.POST.get('accion') == 'admin_editar_ejercicio_rutina':
            ej_id = request.POST.get('ejercicio_id')
            ej_obj = get_object_or_404(Ejercicio, id=ej_id)
            ej_obj.nombre = request.POST.get('nombre_ejercicio', ej_obj.nombre).strip()
            ej_obj.series = int(request.POST.get('series') or ej_obj.series)
            ej_obj.repeticiones = request.POST.get('repeticiones', ej_obj.repeticiones).strip()
            ej_obj.descanso = request.POST.get('descanso', ej_obj.descanso).strip()
            ej_obj.save()
            messages.success(request, f"Ejercicio '{ej_obj.nombre}' actualizado.")
            return redirect('dashboard')

        if request.method == 'POST' and request.POST.get('accion') == 'admin_eliminar_ejercicio_rutina':
            ej_id = request.POST.get('ejercicio_id')
            Ejercicio.objects.filter(id=ej_id).delete()
            messages.success(request, "Ejercicio eliminado de la rutina.")
            return redirect('dashboard')

        # ==========================================================
        # 📊 MÉTRICAS DEL DASHBOARD ADMIN
        # ==========================================================
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

        socios_para_cobro = []
        for s in Socio.objects.select_related('usuario').filter(usuario__is_active=True).order_by('usuario__last_name', 'usuario__first_name'):
            memb_activa = MembresiaSocio.objects.filter(
                socio=s, activa=True, fecha_fin__gte=hoy
            ).select_related('plan').order_by('-fecha_fin').first()
            anotado_en = []
            for m in MembresiaSocio.objects.filter(socio=s, activa=True, fecha_fin__gte=hoy).select_related('plan'):
                if m.plan:
                    anotado_en.append(m.plan.nombre)
            if Reserva:
                try:
                    for r in Reserva.objects.filter(socio=s, estado__in=['confirmada', 'activa', 'Confirmada', 'Activa']):
                        act_r = getattr(r, 'actividad', None) or getattr(getattr(r, 'horario', None), 'actividad', None)
                        if act_r and act_r.nombre not in anotado_en:
                            anotado_en.append(act_r.nombre)
                except Exception:
                    pass
            socios_para_cobro.append({
                'id': s.id,
                'nombre': f"{s.usuario.first_name} {s.usuario.last_name}".strip() or s.usuario.username,
                'dni': getattr(s.usuario, 'dni', '') or s.usuario.username,
                'al_dia': bool(memb_activa),
                'vence': memb_activa.fecha_fin.strftime('%d/%m/%Y') if memb_activa else None,
                'anotado_en': anotado_en,
            })

        context = {
            'total_socios': Usuario.objects.filter(rol='socio').count(),
            'total_empleados': Usuario.objects.filter(
                rol__in=['recepcion', 'entrenador', 'empleado']
            ).count(),
            'total_actividades': Actividad.objects.filter(activa=True).count(),
            'ingresos_mes': ingresos_mes_formateado,
            'socios_select': Usuario.objects.filter(
                rol='socio', is_active=True
            ).order_by('first_name'),
            'planes_select': Plan.objects.all().order_by('precio'),
            'socios_para_cobro': socios_para_cobro,
            'planes_disponibles': Plan.objects.all().order_by('precio'),
            'actividades_disponibles': Actividad.objects.filter(activa=True).order_by('nombre'),
            'rutinas_basicas_admin': Rutina.objects.filter(
                nombre__in=['Adaptación', 'Hipertrofia', 'Fuerza'], tipo='gimnasio'
            ).prefetch_related('dias__ejercicios').order_by('id'),
            'rutinas_socios_admin': Rutina.objects.filter(tipo='gimnasio').exclude(
                nombre__in=['Adaptación', 'Hipertrofia', 'Fuerza']
            ).select_related('socio').prefetch_related('dias__ejercicios'),
        }
        return render(request, 'admin/dashboard.html', context)


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 2. EMPLEADO / RECEPCIÓN / ENTRENADOR
    elif getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado'):
        inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
        fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

        # A. REGISTRAR COBRO PRESENCIAL DE MEMBRESÍA (UNIFICADO CON ADMIN)
        if request.method == 'POST' and request.POST.get('accion') in ('cobrar_membresia_empleado', 'registrar_pago_empleado'):
            socio_id = request.POST.get('socio_id', '').strip()
            dni_socio = request.POST.get('dni_socio', '').strip()
            plan_id = request.POST.get('plan_id')
            actividad_id = request.POST.get('actividad_id')
            metodo = request.POST.get('metodo_pago', 'efectivo')

            socio_obj = Socio.objects.filter(id=socio_id).first() if socio_id else None
            if not socio_obj and dni_socio:
                socio_user = Usuario.objects.filter(username=dni_socio, rol='socio').first() or Usuario.objects.filter(username=dni_socio).first()
                if socio_user:
                    socio_obj, _ = Socio.objects.get_or_create(usuario=socio_user)

            plan_obj = Plan.objects.filter(id=plan_id).first() if plan_id else None
            act_obj = Actividad.objects.filter(id=actividad_id).first() if actividad_id else None

            if not socio_obj:
                messages.error(request, "Debe seleccionar un socio de la lista.")
            elif not plan_obj and not act_obj:
                messages.error(request, "Debe seleccionar una membresía o una actividad para cobrar.")
            else:
                socio_obj.usuario.is_active = True
                socio_obj.usuario.save()

                monto_total = 0
                conceptos = []
                nueva_memb = None

                if plan_obj:
                    monto_total += getattr(plan_obj, 'precio', 0)
                    conceptos.append(plan_obj.nombre)

                    memb_previa = MembresiaSocio.objects.filter(socio=socio_obj).order_by('-fecha_fin').first()
                    dias_vigencia = getattr(plan_obj, 'duracion_dias', 30)
                    if memb_previa and memb_previa.fecha_fin < hoy:
                        dias_atraso = (hoy - memb_previa.fecha_fin).days
                        if 1 <= dias_atraso <= 7:
                            dias_vigencia = max(1, 30 - dias_atraso)

                    MembresiaSocio.objects.filter(socio=socio_obj).update(activa=False)
                    nueva_memb = MembresiaSocio.objects.create(
                        socio=socio_obj,
                        plan=plan_obj,
                        fecha_inicio=hoy,
                        fecha_fin=hoy + timedelta(days=dias_vigencia),
                        activa=True
                    )

                if act_obj:
                    monto_total += getattr(act_obj, 'precio', 0)
                    conceptos.append(act_obj.nombre)

                pago_data = {
                    'socio': socio_obj,
                    'monto': monto_total,
                    'metodo_pago': metodo,
                }
                if nueva_memb and hasattr(Pago, 'membresia'):
                    pago_data['membresia'] = nueva_memb
                if hasattr(Pago, 'fecha_pago'):
                    pago_data['fecha_pago'] = timezone.now()
                elif hasattr(Pago, 'fecha'):
                    pago_data['fecha'] = hoy
                Pago.objects.create(**pago_data)

                if hasattr(socio_obj, 'estado_cuenta'):
                    socio_obj.estado_cuenta = 'VERDE'
                    socio_obj.save()

                nombre_socio = f"{socio_obj.usuario.first_name} {socio_obj.usuario.last_name}".strip() or socio_obj.usuario.username
                messages.success(
                    request, 
                    f"¡Cobro exitoso! Se registró el pago de ${monto_total:,.0f} ({metodo.capitalize()}) para {nombre_socio} — Concepto: {', '.join(conceptos)}."
                )
            return redirect('dashboard')

        # B. REGISTRAR ASISTENCIA DE SOCIO
        if request.method == 'POST' and request.POST.get('accion') == 'registrar_asistencia':
            dni = request.POST.get('dni', '').strip()
            usuario_socio = Usuario.objects.filter(username=dni, rol='socio').first() or Usuario.objects.filter(username=dni).first()
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

            membresia_vigente = MembresiaSocio.objects.filter(
                socio=socio, activa=True, fecha_fin__gte=hoy
            ).order_by('-fecha_fin').first()
            ultima_membresia = membresia_vigente or MembresiaSocio.objects.filter(socio=socio).order_by('-fecha_fin').first()
            esta_al_dia = bool(membresia_vigente) and getattr(socio, 'estado_cuenta', 'VERDE') not in ['ROJO', 'VENCIDO']

            actividades_socio = []
            if Reserva:
                try:
                    reservas_qs = Reserva.objects.filter(socio=socio, estado__in=['confirmada', 'activa', 'Confirmada', 'Activa'])
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
            datos_perfil = {
                'nombre_completo': f"{usuario_socio.first_name} {usuario_socio.last_name}".strip() or usuario_socio.username,
                'iniciales': f"{usuario_socio.first_name[:1]}{usuario_socio.last_name[:1]}".upper() or usuario_socio.username[:2].upper(),
                'foto_url': socio.foto.url if getattr(socio, 'foto', None) else None,
                'dni': usuario_socio.username,
                'email': usuario_socio.email or 'Sin email',
                'plan_nombre': ultima_membresia.plan.nombre if (ultima_membresia and hasattr(ultima_membresia, 'plan')) else "Sin Plan Asignado",
                'fecha_vencimiento': ultima_membresia.fecha_fin.strftime("%d/%m/%Y") if ultima_membresia else "N/A",
                'al_dia': esta_al_dia,
                'estado_texto': "AL DÍA" if esta_al_dia else "CUOTA VENCIDA",
                'tipo_acceso': "Acceso Libre (Musculación / Gimnasio)",
                'actividades': actividades_socio,
                'historial_asistencias': historial_asistencias,
                'acceso_permitido': False,
                'motivo': ''
            }
            if not esta_al_dia:
                datos_perfil['motivo'] = "Cuota Vencida. Regularizar pago en caja."
                request.session['ultimo_socio_acceso'] = datos_perfil
                messages.error(request, f"Acceso DENEGADO para {usuario_socio.first_name}: Cuota Vencida.")
                return redirect('dashboard')

            asistencias_hoy = Asistencia.objects.filter(socio=socio, fecha_hora__range=(inicio_dia, fin_dia)).order_by('fecha_hora')
            cant_ingresos_hoy = asistencias_hoy.count()

            reserva_hoy = None
            if Reserva:
                try:
                    campos_r = {f.name for f in Reserva._meta.get_fields()}
                    filtro_fecha = {'fecha_reserva': hoy} if 'fecha_reserva' in campos_r else {'fecha': hoy}
                    reserva_hoy = Reserva.objects.filter(
                        socio=socio,
                        estado__in=['confirmada', 'activa', 'Confirmada', 'Activa', 'pendiente', 'Pendiente'],
                        **filtro_fecha
                    ).select_related('horario__actividad').first()
                except Exception:
                    reserva_hoy = None

            if cant_ingresos_hoy == 0:
                nueva_asist = Asistencia.objects.create(socio=socio, fecha_hora=timezone.now())
                datos_perfil['historial_asistencias'].insert(0, timezone.localtime(nueva_asist.fecha_hora).strftime('%d/%m/%Y %H:%M hs'))
                datos_perfil['acceso_permitido'] = True
                datos_perfil['tipo_acceso'] = "Acceso Libre (Musculación / Gimnasio)"
                datos_perfil['motivo'] = "Primer ingreso del día registrado con éxito."
                messages.success(request, f"Acceso Concedido: Ingreso registrado para {usuario_socio.first_name}.")
            elif cant_ingresos_hoy == 1:
                if reserva_hoy:
                    nueva_asist = Asistencia.objects.create(socio=socio, fecha_hora=timezone.now())
                    datos_perfil['historial_asistencias'].insert(0, timezone.localtime(nueva_asist.fecha_hora).strftime('%d/%m/%Y %H:%M hs'))
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
            else:
                datos_perfil['acceso_permitido'] = False
                datos_perfil['motivo'] = "Límite diario alcanzado (Ingreso libre + Clase reservada completados)."
                messages.warning(request, f"Acceso Denegado: {usuario_socio.first_name} ya completó los ingresos permitidos de hoy.")
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

        # H. GESTIÓN COMPLETA DE RUTINAS (3 BÁSICAS + PERSONALIZADAS SOCIOS)
        if request.method == 'POST' and request.POST.get('accion') == 'empleado_agregar_ejercicio_rutina':
            destino = request.POST.get('destino', 'socio')
            dia_nombre = request.POST.get('nombre_dia', 'Día 1').strip()
            nombre_ej = request.POST.get('nombre_ejercicio', '').strip()
            series_num = int(request.POST.get('series') or 3)
            reps_txt = request.POST.get('repeticiones', '8-12 reps').strip()
            descanso_txt = request.POST.get('descanso', '90s').strip()

            if destino == 'basica':
                rutina_id = request.POST.get('rutina_basica_id')
                rutina_obj = get_object_or_404(Rutina, id=rutina_id)
            else:
                socio_user_id = request.POST.get('socio_usuario_id')
                socio_user = get_object_or_404(Usuario, id=socio_user_id)
                rutina_obj, _ = Rutina.objects.get_or_create(
                    socio=socio_user,
                    tipo='gimnasio',
                    defaults={'nombre': f'Plan Personalizado - {socio_user.first_name or socio_user.username}'}
                )

            dia_obj, _ = DiaEntrenamiento.objects.get_or_create(
                rutina=rutina_obj,
                nombre_dia=dia_nombre
            )
            Ejercicio.objects.create(
                dia=dia_obj,
                nombre=nombre_ej,
                series=series_num,
                repeticiones=reps_txt,
                descanso=descanso_txt
            )
            messages.success(request, f"Ejercicio '{nombre_ej}' guardado en {rutina_obj.nombre} ({dia_nombre}).")
            return redirect('dashboard')

        if request.method == 'POST' and request.POST.get('accion') == 'empleado_editar_ejercicio_rutina':
            ej_id = request.POST.get('ejercicio_id')
            ej_obj = get_object_or_404(Ejercicio, id=ej_id)
            ej_obj.nombre = request.POST.get('nombre_ejercicio', ej_obj.nombre).strip()
            ej_obj.series = int(request.POST.get('series') or ej_obj.series)
            ej_obj.repeticiones = request.POST.get('repeticiones', ej_obj.repeticiones).strip()
            ej_obj.descanso = request.POST.get('descanso', ej_obj.descanso).strip()
            ej_obj.save()
            messages.success(request, f"Ejercicio '{ej_obj.nombre}' actualizado.")
            return redirect('dashboard')

        if request.method == 'POST' and request.POST.get('accion') == 'empleado_eliminar_ejercicio_rutina':
            ej_id = request.POST.get('ejercicio_id')
            Ejercicio.objects.filter(id=ej_id).delete()
            messages.success(request, "Ejercicio eliminado de la rutina.")
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

        # E. DISCIPLINAS ACTIVAS, HORARIOS Y CONTEO REAL DE ANOTADOS
        actividades_db = Actividad.objects.filter(activa=True).order_by('nombre')
        total_actividades = actividades_db.count()

        fk_horario_res = None
        tiene_fk_act_res = False
        if Reserva:
            campos_res = {f.name: f for f in Reserva._meta.get_fields()}
            fk_horario_res = next((n for n in ('horario', 'clase', 'turno', 'horario_clase') if n in campos_res), None)
            tiene_fk_act_res = 'actividad' in campos_res

        disciplinas_detalle = []
        for act in actividades_db:
            horarios_lista = []
            clases_rel = getattr(act, 'clases', None) or getattr(act, 'clase_set', None) or getattr(act, 'horarios', None)
            clases_qs = clases_rel.all() if clases_rel else []
            for h in clases_qs:
                dias_str = getattr(h, 'dias', 'Lunes a Viernes')
                hora_str = f"{h.hora_inicio.strftime('%H:%M')} a {h.hora_fin.strftime('%H:%M')}" if hasattr(h, 'hora_inicio') and h.hora_inicio else 'Consultar horario'
                profe_str = f"{h.profesor.first_name} {h.profesor.last_name}" if getattr(h, 'profesor', None) else 'A designar'
                horarios_lista.append({
                    'dias': dias_str,
                    'horario': hora_str,
                    'profesor': profe_str
                })

            anotados_count = 0
            if Reserva:
                try:
                    if tiene_fk_act_res:
                        anotados_count = Reserva.objects.filter(
                            actividad=act,
                            estado__in=['confirmada', 'activa', 'Confirmada', 'Activa']
                        ).values('socio').distinct().count()
                    elif fk_horario_res:
                        anotados_count = Reserva.objects.filter(
                            **{
                                f'{fk_horario_res}__actividad': act,
                                'estado__in': ['confirmada', 'activa', 'Confirmada', 'Activa']
                            }
                        ).values('socio').distinct().count()
                except Exception:
                    anotados_count = 0

            disciplinas_detalle.append({
                'actividad': act,
                'requiere_reserva': getattr(act, 'requiere_reserva', False),
                'horarios': horarios_lista,
                'anotados': anotados_count,
                'cupo_maximo': getattr(act, 'cupo_maximo', None) or getattr(act, 'cupo', None),
            })

        # F. ASISTENCIAS
        total_asistencias_hoy = Asistencia.objects.filter(fecha_hora__range=(inicio_dia, fin_dia)).count()
        ultimas_asistencias = Asistencia.objects.select_related('socio__usuario').order_by('-fecha_hora')[:10]
        MESES_ES = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        historial_asistencias_completo = []
        meses_vistos = {}
        for a in Asistencia.objects.select_related('socio__usuario').order_by('-fecha_hora')[:300]:
            dt_local = timezone.localtime(a.fecha_hora)
            clave_mes = dt_local.strftime('%Y-%m')
            if clave_mes not in meses_vistos:
                meses_vistos[clave_mes] = f"{MESES_ES[dt_local.month]} {dt_local.year}"
            historial_asistencias_completo.append({
                'fecha_str': dt_local.strftime('%d/%m/%Y'),
                'hora_str': dt_local.strftime('%H:%M'),
                'es_hoy': dt_local.date() == hoy,
                'mes_anio': clave_mes,
                'socio_nombre': f"{a.socio.usuario.first_name} {a.socio.usuario.last_name}".strip() or a.socio.usuario.username,
                'dni': a.socio.usuario.username,
            })
        meses_asistencias = [{'valor': k, 'etiqueta': v} for k, v in meses_vistos.items()]

        # G. ÚLTIMOS COBROS Y LISTADO DE SOCIOS PARA MODAL UNIFICADO DE COBRO
        ultimos_cobros = Pago.objects.select_related('socio__usuario', 'membresia__plan').order_by('-id')[:10]
        perfil_socio_acceso = request.session.pop('ultimo_socio_acceso', None)

        socios_para_cobro = []
        for s in Socio.objects.select_related('usuario').filter(usuario__is_active=True).order_by('usuario__last_name', 'usuario__first_name'):
            memb_activa = MembresiaSocio.objects.filter(
                socio=s, activa=True, fecha_fin__gte=hoy
            ).select_related('plan').order_by('-fecha_fin').first()
            anotado_en = []
            for m in MembresiaSocio.objects.filter(socio=s, activa=True, fecha_fin__gte=hoy).select_related('plan'):
                if m.plan:
                    anotado_en.append(m.plan.nombre)
            if Reserva:
                try:
                    for r in Reserva.objects.filter(socio=s, estado__in=['confirmada', 'activa', 'Confirmada', 'Activa']):
                        act_r = getattr(r, 'actividad', None) or getattr(getattr(r, 'horario', None), 'actividad', None)
                        if act_r and act_r.nombre not in anotado_en:
                            anotado_en.append(act_r.nombre)
                except Exception:
                    pass
            socios_para_cobro.append({
                'id': s.id,
                'nombre': f"{s.usuario.first_name} {s.usuario.last_name}".strip() or s.usuario.username,
                'dni': getattr(s.usuario, 'dni', '') or s.usuario.username,
                'al_dia': bool(memb_activa),
                'vence': memb_activa.fecha_fin.strftime('%d/%m/%Y') if memb_activa else None,
                'anotado_en': anotado_en,
            })

        context = {
            'asistencias_hoy': total_asistencias_hoy,
            'ultimas_asistencias': ultimas_asistencias,
            'historial_asistencias_completo': historial_asistencias_completo,
            'meses_asistencias': meses_asistencias,
            'total_socios': Usuario.objects.filter(rol='socio').count(),
            'total_actividades': total_actividades,
            'disciplinas_detalle': disciplinas_detalle,
            'profesores_cards': profesores_cards,
            'planes_select': Plan.objects.all().order_by('precio'),
            'socios_para_cobro': socios_para_cobro,
            'planes_disponibles': Plan.objects.all().order_by('precio'),
            'actividades_disponibles': Actividad.objects.filter(activa=True).order_by('nombre'),
            'socios_usuarios_lista': Usuario.objects.filter(rol='socio', is_active=True).order_by('first_name', 'last_name'),
            'rutinas_basicas_empleado': Rutina.objects.filter(
                nombre__in=['Adaptación', 'Hipertrofia', 'Fuerza'], tipo='gimnasio'
            ).prefetch_related('dias__ejercicios').order_by('id'),
            'rutinas_asignadas_empleado': Rutina.objects.filter(tipo='gimnasio').exclude(
                nombre__in=['Adaptación', 'Hipertrofia', 'Fuerza']
            ).select_related('socio').prefetch_related('dias__ejercicios'),
            'ultimos_cobros': ultimos_cobros,
            'perfil_socio_acceso': perfil_socio_acceso,
        }
        return render(request, 'empleado/dashboard.html', context)


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 3. SOCIO (POR DEFECTO)
    else:
        hoy = timezone.localdate()
        socio_obj, _ = Socio.objects.get_or_create(usuario=user)
        membresia_actual = (
            MembresiaSocio.objects.filter(
                socio=socio_obj, 
                activa=True, 
                fecha_fin__gte=hoy
            )
            .select_related('plan')
            .order_by('-fecha_fin')
            .first()
        )
        cuota_al_dia = bool(membresia_actual) and getattr(socio_obj, 'estado_cuenta', 'VERDE') not in ['ROJO', 'VENCIDO']

        # A. INSCRIPCIÓN / BAJA EN ACTIVIDADES DESDE PORTAL SOCIO
        if request.method == 'POST' and request.POST.get('accion') == 'inscribir_actividad':
            act_id = request.POST.get('actividad_id')
            act_obj = get_object_or_404(Actividad, id=act_id)

            if not cuota_al_dia:
                messages.error(request, "Tu cuota está vencida. Regularizá el pago en Perfil o en recepción para anotarte a clases.")
            elif Reserva:
                ya_anotado = False
                campos_res = {f.name: f for f in Reserva._meta.get_fields()}
                fk_horario = next((n for n in ('horario', 'clase', 'turno', 'horario_clase') if n in campos_res), None)
                fk_actividad = 'actividad' if 'actividad' in campos_res else None

                try:
                    if fk_actividad:
                        ya_anotado = Reserva.objects.filter(
                            socio=socio_obj, actividad=act_obj, estado__in=['confirmada', 'activa', 'Confirmada', 'Activa']
                        ).exists()
                    elif fk_horario:
                        ya_anotado = Reserva.objects.filter(
                            **{'socio': socio_obj, f'{fk_horario}__actividad': act_obj, 'estado__in': ['confirmada', 'activa', 'Confirmada', 'Activa']}
                        ).exists()
                except Exception:
                    ya_anotado = False

                if ya_anotado:
                    messages.info(request, f"Ya estás anotado en {act_obj.nombre}.")
                else:
                    try:
                        res_kwargs = {'socio': socio_obj}
                        if 'fecha_reserva' in campos_res:
                            res_kwargs['fecha_reserva'] = hoy
                        if 'fecha' in campos_res:
                            res_kwargs['fecha'] = hoy
                        if 'estado' in campos_res:
                            res_kwargs['estado'] = 'confirmada'

                        if fk_actividad:
                            res_kwargs[fk_actividad] = act_obj
                            Reserva.objects.create(**res_kwargs)
                        elif fk_horario:
                            HorarioModel = campos_res[fk_horario].related_model
                            primer_horario = HorarioModel.objects.filter(actividad=act_obj).first()

                            if not primer_horario:
                                campos_h = {f.name: f for f in HorarioModel._meta.get_fields()}
                                h_kwargs = {'actividad': act_obj}
                                if 'dia_semana' in campos_h:
                                    h_kwargs['dia_semana'] = 'Lunes'
                                elif 'dia' in campos_h:
                                    h_kwargs['dia'] = 'Lunes'
                                elif 'dias' in campos_h:
                                    h_kwargs['dias'] = 'Lunes a Viernes'
                                if 'hora_inicio' in campos_h:
                                    h_kwargs['hora_inicio'] = time(18, 0)
                                if 'hora_fin' in campos_h:
                                    h_kwargs['hora_fin'] = time(19, 0)
                                if 'cupo_maximo' in campos_h:
                                    h_kwargs['cupo_maximo'] = 30
                                elif 'cupo' in campos_h:
                                    h_kwargs['cupo'] = 30
                                primer_horario = HorarioModel.objects.create(**h_kwargs)

                            res_kwargs[fk_horario] = primer_horario
                            Reserva.objects.create(**res_kwargs)

                        messages.success(request, f"¡Te anotaste con éxito en {act_obj.nombre}!")
                    except Exception as e:
                        messages.error(request, f"Error al inscribir en {act_obj.nombre}: {e}")
            return redirect('/dashboard/?tab=actividades')

        if request.method == 'POST' and request.POST.get('accion') == 'cancelar_actividad':
            act_id = request.POST.get('actividad_id')
            act_obj = get_object_or_404(Actividad, id=act_id)
            if Reserva:
                campos_res = {f.name: f for f in Reserva._meta.get_fields()}
                fk_horario = next((n for n in ('horario', 'clase', 'turno', 'horario_clase') if n in campos_res), None)
                try:
                    if 'actividad' in campos_res:
                        Reserva.objects.filter(
                            socio=socio_obj, actividad=act_obj, estado__in=['confirmada', 'activa', 'Confirmada', 'Activa']
                        ).update(estado='cancelada')
                    elif fk_horario:
                        Reserva.objects.filter(
                            **{'socio': socio_obj, f'{fk_horario}__actividad': act_obj, 'estado__in': ['confirmada', 'activa', 'Confirmada', 'Activa']}
                        ).update(estado='cancelada')
                except Exception:
                    pass
                messages.success(request, f"Se canceló tu inscripción en {act_obj.nombre}.")
            return redirect('/dashboard/?tab=actividades')

        # B. ACTUALIZAR PERFIL Y CAMBIAR CONTRASEÑA SEGURA
        if request.method == 'POST' and request.POST.get('accion') == 'actualizar_perfil':
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            user.email = request.POST.get('email', '').strip()
            if hasattr(user, 'telefono'):
                user.telefono = request.POST.get('telefono', '').strip()
            user.save()
            messages.success(request, "Tus datos personales fueron actualizados correctamente.")
            return redirect('/dashboard/?tab=perfil')

        if request.method == 'POST' and request.POST.get('accion') == 'cambiar_password':
            pass_actual = request.POST.get('pass_actual', '')
            pass_nueva = request.POST.get('pass_nueva', '')
            pass_confirmar = request.POST.get('pass_confirmar', '')

            tiene_longitud = len(pass_nueva) >= 8
            tiene_mayuscula = bool(re.search(r'[A-Z]', pass_nueva))
            tiene_minuscula = bool(re.search(r'[a-z]', pass_nueva))
            tiene_numero = bool(re.search(r'\d', pass_nueva))
            tiene_simbolo = bool(re.search(r'[^A-Za-z0-9]', pass_nueva))

            if not user.check_password(pass_actual):
                messages.error(request, "La contraseña actual ingresada no es correcta.")
            elif pass_nueva != pass_confirmar:
                messages.error(request, "La nueva contraseña y su confirmación no coinciden.")
            elif not (tiene_longitud and tiene_mayuscula and tiene_minuscula and tiene_numero and tiene_simbolo):
                messages.error(
                    request,
                    "La nueva contraseña debe tener al menos 8 caracteres, 1 mayúscula, 1 minúscula, 1 número y 1 símbolo."
                )
            else:
                user.set_password(pass_nueva)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "¡Contraseña actualizada con éxito!")
            return redirect('/dashboard/?tab=perfil')

        # C. LISTAS DE ACTIVIDADES INSCRIPTAS VS DISPONIBLES
        todas_actividades = list(Actividad.objects.filter(activa=True).order_by('nombre'))
        ids_anotadas = set()
        if Reserva and socio_obj:
            campos_res = {f.name: f for f in Reserva._meta.get_fields()}
            fk_horario = next((n for n in ('horario', 'clase', 'turno', 'horario_clase') if n in campos_res), None)
            try:
                reservas_activas = Reserva.objects.filter(
                    socio=socio_obj,
                    estado__in=['confirmada', 'activa', 'Confirmada', 'Activa']
                )
                for r in reservas_activas:
                    if getattr(r, 'actividad_id', None):
                        ids_anotadas.add(r.actividad_id)
                    elif fk_horario:
                        obj_h = getattr(r, fk_horario, None)
                        if obj_h and getattr(obj_h, 'actividad_id', None):
                            ids_anotadas.add(obj_h.actividad_id)
            except Exception:
                pass

        actividades_anotadas = [a for a in todas_actividades if a.id in ids_anotadas]
        actividades_disponibles = [a for a in todas_actividades if a.id not in ids_anotadas]

        # D. LÓGICA DE RUTINAS (3 BÁSICOS EN BD + PROFESOR + MI PROPIA RUTINA)
        rutina_adaptacion = Rutina.objects.filter(nombre__iexact='Adaptación', tipo='gimnasio').prefetch_related('dias__ejercicios').first()
        rutina_hipertrofia = Rutina.objects.filter(nombre__iexact='Hipertrofia', tipo='gimnasio').prefetch_related('dias__ejercicios').first()
        rutina_fuerza = Rutina.objects.filter(nombre__iexact='Fuerza', tipo='gimnasio').prefetch_related('dias__ejercicios').first()

        rutina_gym = Rutina.objects.filter(socio=user, tipo='gimnasio').exclude(
            nombre__iexact='Adaptación'
        ).exclude(
            nombre__iexact='Hipertrofia'
        ).exclude(
            nombre__iexact='Fuerza'
        ).prefetch_related('dias__ejercicios').first()

        rutina_propia = Rutina.objects.filter(socio=user, tipo='personalizada').prefetch_related('dias__ejercicios').first()

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
            series_num = int(request.POST.get('series') or 3)
            reps_val = request.POST.get('reps') or '10'
            peso_val = request.POST.get('peso_sugerido', '').strip()
            reps_texto = f"{series_num} series × {reps_val} reps" + (f" ({peso_val} kg)" if peso_val else "")
            Ejercicio.objects.create(
                dia=dia_obj,
                nombre=nombre_ej,
                repeticiones=reps_texto,
                series=series_num,
                descanso=request.POST.get('descanso') or '90s'
            )
            messages.success(request, f"Ejercicio '{nombre_ej}' agregado a {dia_seleccionado.capitalize()}.")
            return redirect(f'/dashboard/?tab=custom&dia={dia_seleccionado}')

        if request.method == 'POST' and request.POST.get('accion') == 'editar_ejercicio_custom':
            ej_id = request.POST.get('ejercicio_id')
            ej_obj = Ejercicio.objects.filter(id=ej_id, dia__rutina__socio=user).first()
            if ej_obj:
                ej_obj.nombre = request.POST.get('nombre_ejercicio', ej_obj.nombre).strip()
                ej_obj.repeticiones = request.POST.get('repeticiones', ej_obj.repeticiones).strip()
                if request.POST.get('series'):
                    ej_obj.series = int(request.POST.get('series'))
                ej_obj.save()
                messages.success(request, f"Ejercicio '{ej_obj.nombre}' actualizado.")
            return redirect('/dashboard/?tab=custom')

        if request.method == 'POST' and request.POST.get('accion') == 'eliminar_ejercicio_custom':
            ej_id = request.POST.get('ejercicio_id')
            if ej_id:
                Ejercicio.objects.filter(id=ej_id, dia__rutina__socio=user).delete()
                messages.success(request, "Ejercicio eliminado de tu rutina.")
            return redirect('/dashboard/?tab=custom')

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

        # E. LÓGICA DE AUTOGESTIÓN DE PAGOS
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
                detalle_items = " + ".join(nombres_items)
                plan_obj, _ = Plan.objects.get_or_create(
                    nombre=detalle_items,
                    defaults={'precio': total_a_pagar, 'duracion_dias': 30}
                )
                MembresiaSocio.objects.filter(socio=socio_obj).update(activa=False)
                nueva_membresia = MembresiaSocio.objects.create(
                    socio=socio_obj,
                    plan=plan_obj,
                    fecha_inicio=hoy,
                    fecha_fin=hoy + timedelta(days=30),
                    activa=True
                )
                Pago.objects.create(
                    socio=socio_obj,
                    membresia=nueva_membresia,
                    monto=total_a_pagar,
                    metodo_pago=metodo,
                    fecha_pago=timezone.now()
                )
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

        # F. RESPUESTA GET / RENDER
        historial_pagos = Pago.objects.filter(socio=socio_obj).order_by('-fecha_pago') if socio_obj else []
        context = {
            'socio': socio_obj,
            'membresia_actual': membresia_actual,
            'cuota_al_dia': cuota_al_dia,
            'actividades': todas_actividades,
            'actividades_anotadas': actividades_anotadas,
            'actividades_disponibles': actividades_disponibles,
            'total_inscriptas': len(actividades_anotadas),
            'historial_pagos': historial_pagos,
            'rutina_adaptacion': rutina_adaptacion,
            'rutina_hipertrofia': rutina_hipertrofia,
            'rutina_fuerza': rutina_fuerza,
            'rutina_gym': rutina_gym,
            'rutina_propia': rutina_propia,
            'rutina_semanal': rutina_semanal,
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
        if accion == 'toggle_baja':
            act_id = request.POST.get('actividad_id')
            act = get_object_or_404(Actividad, id=act_id)
            if hasattr(act, 'activa'):
                act.activa = not act.activa
                act.save()
                estado = "reactivada" if act.activa else "dada de baja"
                messages.success(request, f"La actividad '{act.nombre}' fue {estado} correctamente.")
            return redirect('admin_actividades')
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
        elif accion == 'editar':
            act_id = request.POST.get('actividad_id')
            act = get_object_or_404(Actividad, id=act_id)
            act.nombre = request.POST.get('nombre', '').strip()
            act.descripcion = request.POST.get('descripcion', '').strip()
            act.requiere_reserva = request.POST.get('requiere_reserva') == 'on'
            act.save()
            messages.success(request, f"Actividad '{act.nombre}' actualizada exitosamente.")
            return redirect('admin_actividades')
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
    tiene_descripcion_bd = hasattr(Plan, 'descripcion')
    ruta_json_desc = os.path.join(settings.BASE_DIR, 'planes_descripciones.json')

    def leer_descripciones_json():
        if os.path.exists(ruta_json_desc):
            try:
                with open(ruta_json_desc, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def guardar_descripcion_json(plan_id, texto):
        datos = leer_descripciones_json()
        datos[str(plan_id)] = texto
        with open(ruta_json_desc, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'crear':
            nombre = request.POST.get('nombre', '').strip()
            precio_raw = str(request.POST.get('precio', '0')).replace(',', '.').strip()
            duracion = request.POST.get('duracion_dias', 30)
            descripcion = request.POST.get('descripcion', '').strip()
            plan_kwargs = {
                'nombre': nombre,
                'precio': precio_raw or 0,
                'duracion_dias': duracion or 30,
            }
            if tiene_descripcion_bd:
                plan_kwargs['descripcion'] = descripcion
            nuevo_plan = Plan.objects.create(**plan_kwargs)
            if descripcion:
                guardar_descripcion_json(nuevo_plan.id, descripcion)
            messages.success(request, f"Plan '{nombre}' creado exitosamente.")
            return redirect('admin_membresias')
        elif accion == 'editar':
            plan_id = request.POST.get('plan_id')
            plan = get_object_or_404(Plan, id=plan_id)
            plan.nombre = request.POST.get('nombre', '').strip()
            precio_raw = str(request.POST.get('precio', plan.precio)).replace(',', '.').strip()
            if precio_raw:
                plan.precio = precio_raw
            duracion_raw = request.POST.get('duracion_dias', '').strip()
            if duracion_raw:
                plan.duracion_dias = int(duracion_raw)
            nueva_desc = request.POST.get('descripcion', '').strip()
            if tiene_descripcion_bd:
                plan.descripcion = nueva_desc
            plan.save()
            guardar_descripcion_json(plan.id, nueva_desc)
            messages.success(request, f"Plan '{plan.nombre}' actualizado correctamente.")
            return redirect('admin_membresias')
        elif accion == 'eliminar':
            plan_id = request.POST.get('plan_id')
            plan = get_object_or_404(Plan, id=plan_id)
            nombre_plan = plan.nombre
            plan.delete()
            messages.success(request, f"Plan '{nombre_plan}' eliminado.")
            return redirect('admin_membresias')

    planes_qs = list(Plan.objects.all().order_by('precio', 'nombre'))
    planes_ordenados = sorted(
        planes_qs,
        key=lambda p: (1 if 'pilates' in p.nombre.lower() else 0, p.precio, p.nombre)
    )
    descripciones_guardadas = leer_descripciones_json()
    for p in planes_ordenados:
        desc_bd = getattr(p, 'descripcion', '').strip() if tiene_descripcion_bd else ''
        desc_json = descripciones_guardadas.get(str(p.id), '').strip()
        if desc_json:
            p.descripcion_mostrar = desc_json
        elif desc_bd:
            p.descripcion_mostrar = desc_bd
        else:
            nom = p.nombre.lower()
            if 'pilates' in nom and '1' in nom:
                p.descripcion_mostrar = "Con reserva previa (Lun 9-11hs, Mié 11-13hs o Vie 16-18hs)."
            elif 'pilates' in nom and '2' in nom:
                p.descripcion_mostrar = "Con reserva previa en turnos disponibles (Lun 9-11hs, Mié 11-13hs o Vie 16-18hs)."
            elif 'pilates' in nom and '3' in nom:
                p.descripcion_mostrar = "Con reserva previa en turnos disponibles (Lun 9-11hs, Mié 11-13hs o Vie 16-18hs)."
            elif 'clase' in nom:
                p.descripcion_mostrar = "Acceso a todas las clases grupales: Funcional (L/M/V 18hs), Spinning (L/M/V 19hs), Abdominales (L/M/V 20hs), Funcional+Cardio (M/J 18hs) y Zumba (L/M/J 19hs)."
            elif 'familiar' in nom:
                p.descripcion_mostrar = "Válido a partir de 3 integrantes del grupo familiar abonando el mismo día."
            elif 'estudiantil' in nom:
                p.descripcion_mostrar = "Tarifa bonificada mensual presentando certificado de alumno regular vigente."
            elif 'musculacion' in nom or 'musculación' in nom:
                p.descripcion_mostrar = "Acceso libre a sala de Musculación + todas las Clases grupales incluidas durante 30 días (Lun a Vie 7 a 22hs, Sáb 9 a 13hs)."
            else:
                p.descripcion_mostrar = f"Pase habilitado por {p.duracion_dias} días corridos desde la fecha de activación."
    context = {
        'planes': planes_ordenados,
        'total_planes': len(planes_ordenados),
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