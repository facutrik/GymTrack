from datetime import datetime, time, timedelta
from urllib.parse import urlencode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from usuarios.models import Usuario
from socios.models import Socio
from membresias.models import MembresiaSocio, Plan
from actividades.models import Actividad, Clase
from reservas.models import Reserva
from pagos.models import Pago
from asistencias.models import Asistencia

ROLES_PADRON = ('admin', 'recepcion', 'empleado', 'entrenador')


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PADRÓN DE SOCIOS (compartido por el módulo admin y el módulo empleado)
#
# Las dos pantallas muestran lo mismo y permiten las mismas acciones; solo cambia
# el nombre de la URL a la que se vuelve después de cada acción.

def _alta_socio(request, hoy):
    dni = request.POST.get('dni', '').strip()
    nombre = request.POST.get('nombre', '').strip()
    apellido = request.POST.get('apellido', '').strip()
    email = request.POST.get('email', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    plan_id = request.POST.get('plan_id')
    actividad_id = request.POST.get('actividad_id')
    metodo_pago = request.POST.get('metodo_pago', 'efectivo')

    if Usuario.objects.filter(username=dni).exists():
        messages.error(request, f'El DNI {dni} ya está registrado en el sistema.')
        return

    nuevo_user = Usuario.objects.create_user(
        username=dni, email=email, password=dni,
        first_name=nombre, last_name=apellido,
    )
    nuevo_user.rol = 'socio'
    nuevo_user.dni = dni
    nuevo_user.telefono = telefono
    nuevo_user.save()
    socio_obj = Socio.para_usuario(nuevo_user)
    if telefono:
        socio_obj.telefono = telefono
        socio_obj.save(update_fields=['telefono'])

    # Membresía, inscripción y cobro inicial (opcionales)
    plan_obj = Plan.objects.filter(id=plan_id).first() if plan_id else None
    act_obj = Actividad.objects.filter(id=actividad_id).first() if actividad_id else None
    if not (plan_obj or act_obj):
        messages.success(request, f'Socio {nombre} {apellido} registrado (sin cobro inicial). Usuario y clave: {dni}')
        return

    membresia = MembresiaSocio.renovar(socio_obj, plan_obj, hoy) if plan_obj else None
    if act_obj and not act_obj.sin_turno:
        clase = Reserva.clase_de(act_obj) or Clase.objects.create(actividad=act_obj)
        Reserva.objects.create(socio=socio_obj, clase=clase, fecha_reserva=hoy)

    monto = plan_obj.precio if plan_obj else 0
    if monto > 0:
        Pago.objects.create(socio=socio_obj, membresia=membresia, monto=monto, metodo_pago=metodo_pago)
        nuevo_user.estado_cuenta = 'VERDE'
        nuevo_user.save(update_fields=['estado_cuenta'])
        messages.success(
            request,
            f'Socio {nombre} {apellido} dado de alta y cobrado (${monto:,.0f} - {metodo_pago.capitalize()}). Usuario y clave: {dni}'
        )
    else:
        messages.success(request, f'Socio {nombre} {apellido} registrado. Usuario y clave: {dni}')


def _editar_socio(request):
    socio_user = get_object_or_404(Usuario, id=request.POST.get('socio_id'), rol='socio')
    socio_user.first_name = request.POST.get('nombre', '').strip()
    socio_user.last_name = request.POST.get('apellido', '').strip()
    socio_user.email = request.POST.get('email', '').strip()
    socio_user.telefono = request.POST.get('telefono', '').strip()
    socio_user.save()
    perfil = Socio.objects.filter(usuario=socio_user).first()
    if perfil:
        perfil.nombre = socio_user.first_name[:100]
        perfil.apellido = socio_user.last_name[:100]
        perfil.email = socio_user.email
        perfil.telefono = socio_user.telefono
        perfil.save()
    messages.success(request, f'Datos de {socio_user.get_full_name() or socio_user.username} actualizados.')


def _toggle_baja_socio(request):
    socio_user = get_object_or_404(Usuario, id=request.POST.get('socio_id'), rol='socio')
    socio_user.is_active = not socio_user.is_active
    socio_user.save()
    estado = 'activo' if socio_user.is_active else 'dado de baja'
    messages.success(request, f'El socio {socio_user.get_full_name() or socio_user.username} ahora está {estado}.')


def _listar_socios(request, hoy):
    """Socios filtrados por búsqueda y estado, con el semáforo de cuota y la baja automática a los 90 días."""
    limite_3_meses = hoy - timedelta(days=90)
    query = request.GET.get('q', '').strip()
    filtro_estado = request.GET.get('estado', 'todos')

    socios_qs = Usuario.objects.filter(rol='socio').order_by('-date_joined')
    if query:
        socios_qs = socios_qs.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    socios_lista = []
    for s in socios_qs:
        socio_obj = Socio.objects.filter(usuario=s).first()
        ultima_memb = (
            MembresiaSocio.objects.filter(socio=socio_obj).order_by('-fecha_fin').first()
            if socio_obj else None
        )
        vigente = bool(ultima_memb and ultima_memb.activa and ultima_memb.fecha_fin >= hoy)
        sin_movimiento = (
            ultima_memb.fecha_fin < limite_3_meses if ultima_memb
            else s.date_joined.date() < limite_3_meses
        )
        if s.is_active and not vigente and sin_movimiento:
            s.is_active = False
            s.save(update_fields=['is_active'])

        estado_cuota = 'VERDE' if vigente else 'ROJO'
        if s.estado_cuenta != estado_cuota:
            s.estado_cuenta = estado_cuota
            s.save(update_fields=['estado_cuenta'])

        if filtro_estado == 'activos' and not s.is_active:
            continue
        if filtro_estado == 'inactivos' and s.is_active:
            continue
        socios_lista.append({
            'usuario': s,
            'socio': socio_obj,
            'estado_cuota': estado_cuota,
            'ultimo_vencimiento': ultima_memb.fecha_fin if ultima_memb else None,
        })
    return socios_lista, query, filtro_estado


def _perfil_socio(usuario_id, hoy):
    """Datos para el cartel "Ver perfil" del padrón (None si el id no es de un socio)."""
    s = Usuario.objects.filter(id=usuario_id, rol='socio').first() if str(usuario_id).isdigit() else None
    if not s:
        return None
    perfil = Socio.objects.filter(usuario=s).first()
    membresias = MembresiaSocio.objects.filter(socio=perfil).select_related('plan') if perfil else MembresiaSocio.objects.none()
    vigente = membresias.filter(activa=True, fecha_fin__gte=hoy).order_by('-fecha_fin').first()
    ultima = vigente or membresias.order_by('-fecha_fin').first()
    inicio_mes = timezone.make_aware(datetime.combine(hoy.replace(day=1), time.min))

    clases = []
    pagos, asistencias, asistencias_mes = [], [], 0
    if perfil:
        reservas = Reserva.objects.filter(socio=perfil, estado='confirmada').select_related('clase__actividad')
        clases = list(dict.fromkeys(r.clase.actividad.nombre for r in reservas))
        pagos = Pago.objects.filter(socio=perfil).select_related('membresia__plan').order_by('-fecha_pago')[:5]
        asistencias_qs = Asistencia.objects.filter(socio=perfil)
        asistencias = asistencias_qs.order_by('-fecha_hora')[:5]
        asistencias_mes = asistencias_qs.filter(fecha_hora__gte=inicio_mes).count()

    return {
        'usuario': s,
        'perfil': perfil,
        'al_dia': bool(vigente),
        'membresia': ultima,
        'dias_restantes': (vigente.fecha_fin - hoy).days if vigente else None,
        'clases': clases,
        'pagos': pagos,
        'asistencias': asistencias,
        'asistencias_mes': asistencias_mes,
    }


def _padron_socios(request, url_padron):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in ROLES_PADRON):
        return redirect('dashboard')
    hoy = timezone.localdate()

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'alta':
            _alta_socio(request, hoy)
        elif accion == 'editar':
            _editar_socio(request)
        elif accion == 'toggle_baja':
            _toggle_baja_socio(request)
        return redirect(url_padron)

    socios_lista, query, filtro_estado = _listar_socios(request, hoy)
    context = {
        'url_padron': url_padron,
        'filtros_qs': urlencode({k: v for k, v in (('q', query), ('estado', filtro_estado)) if v and v != 'todos'}),
        'perfil_abierto': _perfil_socio(request.GET.get('perfil'), hoy),
        'socios': socios_lista,
        'query': query,
        'filtro_estado': filtro_estado,
        'total_socios': len(socios_lista),
        'planes_disponibles': Plan.objects.all().order_by('precio'),
        'actividades_disponibles': Actividad.objects.filter(activa=True).order_by('nombre'),
    }
    return render(request, 'compartido/padron_socios.html', context)


# 1. MODULO ADMIN
@login_required
def admin_socios(request):
    return _padron_socios(request, 'admin_socios')


# 2. MÓDULO EMPLEADO
@login_required
def padron_socios_empleado(request):
    return _padron_socios(request, 'padron_socios_empleado')
