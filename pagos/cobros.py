"""
Cobro presencial a socios: lo usan el panel del admin, el del empleado y la página de Pagos
(las tres muestran el mismo modal, templates/includes/modal_cobro.html).
"""
from django.contrib import messages

from actividades.models import Actividad, Clase
from membresias.models import MembresiaSocio, Plan
from pagos.models import Pago
from reservas.models import Reserva
from socios.models import Socio
from usuarios.models import Usuario

# 'registrar_cobro' es la acción del modal; las otras son nombres viejos que se siguen aceptando
ACCIONES_COBRO = ('registrar_cobro', 'cobrar_desde_admin', 'cobrar_membresia_empleado', 'registrar_pago_empleado')

DIAS_DE_GRACIA = 7


def socios_para_cobro(hoy):
    """Socios activos con su estado de cuota y en qué planes y clases están anotados."""
    lista = []
    socios = Socio.objects.select_related('usuario').filter(usuario__is_active=True)
    for s in socios.order_by('usuario__last_name', 'usuario__first_name'):
        vigentes = list(
            MembresiaSocio.objects.filter(socio=s, activa=True, fecha_fin__gte=hoy)
            .select_related('plan').order_by('-fecha_fin')
        )
        anotado_en = [m.plan.nombre for m in vigentes]
        reservas = Reserva.objects.filter(socio=s, estado='confirmada').select_related('clase__actividad')
        for r in reservas:
            if r.clase.actividad.nombre not in anotado_en:
                anotado_en.append(r.clase.actividad.nombre)
        lista.append({
            'id': s.id,
            'nombre': s.usuario.get_full_name() or s.usuario.username,
            'dni': s.usuario.dni or s.usuario.username,
            'al_dia': bool(vigentes),
            'vence': vigentes[0].fecha_fin.strftime('%d/%m/%Y') if vigentes else None,
            'anotado_en': anotado_en,
        })
    return lista


def contexto_cobro(hoy):
    """Lo que necesita el modal de cobro en el contexto del template."""
    return {
        'socios_para_cobro': socios_para_cobro(hoy),
        'planes_disponibles': Plan.objects.all().order_by('precio'),
        'actividades_disponibles': Actividad.objects.filter(activa=True).order_by('nombre'),
    }


def activar_plan(socio, plan, hoy):
    """Activa el plan pagado. Si renueva con hasta 7 días de atraso, el período se cuenta desde el
    vencimiento anterior (lo dicen los Términos y Condiciones, punto 4)."""
    dias = plan.duracion_dias or 30
    previa = MembresiaSocio.objects.filter(socio=socio).order_by('-fecha_fin').first()
    if previa and previa.fecha_fin < hoy:
        atraso = (hoy - previa.fecha_fin).days
        if atraso <= DIAS_DE_GRACIA:
            dias = max(1, dias - atraso)
    return MembresiaSocio.renovar(socio, plan, hoy, dias)


def _inscribir(socio, actividad, hoy):
    """Anota al socio en la actividad (si hace falta turno y no estaba anotado)."""
    if actividad.sin_turno:
        return False
    if Reserva.objects.filter(socio=socio, clase__actividad=actividad, estado='confirmada').exists():
        return False
    clase = Reserva.clase_de(actividad) or Clase.objects.create(actividad=actividad)
    Reserva.objects.create(socio=socio, clase=clase, fecha_reserva=hoy)
    return True


def registrar_cobro(request, hoy):
    """Procesa el POST del modal de cobro y deja el resultado en los mensajes."""
    socio_id = request.POST.get('socio_id', '').strip()
    dni_socio = request.POST.get('dni_socio', '').strip()
    plan_id = request.POST.get('plan_id')
    actividad_id = request.POST.get('actividad_id')
    metodo = request.POST.get('metodo_pago', 'efectivo')

    socio = Socio.objects.select_related('usuario').filter(id=socio_id).first() if socio_id.isdigit() else None
    if not socio and dni_socio:
        socio_user = Usuario.objects.filter(username=dni_socio, rol='socio', is_superuser=False).first()
        socio = Socio.para_usuario(socio_user) if socio_user else None
    plan = Plan.objects.filter(id=plan_id).first() if plan_id else None
    actividad = Actividad.objects.filter(id=actividad_id).first() if actividad_id else None

    if not socio or not socio.usuario:
        messages.error(request, 'Seleccioná un socio de la lista para registrar el cobro.')
        return
    if not plan and not actividad:
        messages.error(request, 'Seleccioná una membresía o una actividad para cobrar.')
        return

    usuario = socio.usuario
    nombre_socio = usuario.get_full_name() or usuario.username
    conceptos = []
    membresia = None

    if plan:
        membresia = activar_plan(socio, plan, hoy)
        conceptos.append(plan.nombre)

    if actividad:
        _inscribir(socio, actividad, hoy)
        conceptos.append(actividad.nombre)

    monto = (plan.precio if plan else 0) + (getattr(actividad, 'precio', 0) or 0)
    usuario.is_active = True
    if monto > 0:
        Pago.objects.create(socio=socio, membresia=membresia, monto=monto, metodo_pago=metodo)
        usuario.estado_cuenta = 'VERDE'
    usuario.save()

    if monto > 0:
        importe = f'{monto:,.0f}'.replace(',', '.')
        messages.success(
            request,
            f"Cobro registrado: ${importe} ({metodo.capitalize()}) a {nombre_socio} — {', '.join(conceptos)}."
        )
    else:
        messages.success(request, f"{nombre_socio} quedó anotado en {', '.join(conceptos)}.")
