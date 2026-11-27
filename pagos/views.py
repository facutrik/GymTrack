import re
from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max, Min, Q, Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from pagos.avisos import avisar_solicitud_recibida, avisar_solicitud_resuelta
from pagos.cobros import ACCIONES_COBRO, activar_plan, contexto_cobro, registrar_cobro
from pagos.models import DIAS_ARREPENTIMIENTO, Pago, SolicitudArrepentimiento

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
         'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']


def _formatear_ars(valor):
    numero = valor or 0
    return (
        f'{numero:,.2f}'.replace(',', 'X')
        .replace('.', ',')
        .replace('X', '.')
    )


def _pagos_ultimos_dias(dias, hoy):
    """Cobros confirmados de los últimos `dias` días contando hoy, y la fecha desde la que se cuentan."""
    desde = hoy - timedelta(days=dias - 1)
    inicio = timezone.make_aware(datetime.combine(desde, time.min))
    return Pago.objects.confirmados().filter(fecha_pago__gte=inicio), desde


def _sumar(pagos):
    return pagos.aggregate(total=Sum('monto'))['total'] or 0


def _nombre_socio(pago):
    usuario = pago.socio.usuario
    return (usuario.get_full_name() or usuario.username) if usuario else str(pago.socio)


# --------------------------------------------------------------------------------------------------
# ACCIONES DE CAJA: confirmar pagos hechos desde la web y resolver arrepentimientos
def _confirmar_pago(request, hoy):
    pago = get_object_or_404(Pago.objects.pendientes(), id=request.POST.get('pago_id'))
    with transaction.atomic():
        if pago.plan:
            pago.membresia = activar_plan(pago.socio, pago.plan, hoy)
        pago.estado = Pago.CONFIRMADO
        pago.save(update_fields=['membresia', 'estado'])
        if pago.socio.usuario:
            pago.socio.usuario.estado_cuenta = 'VERDE'
            pago.socio.usuario.is_active = True
            pago.socio.usuario.save(update_fields=['estado_cuenta', 'is_active'])
    messages.success(request, f'Pago #REC-{pago.id} de {_nombre_socio(pago)} confirmado: {pago.concepto} quedó activo.')


def _rechazar_pago(request):
    pago = get_object_or_404(Pago.objects.pendientes(), id=request.POST.get('pago_id'))
    pago.estado = Pago.RECHAZADO
    pago.save(update_fields=['estado'])
    messages.success(request, f'Pago #REC-{pago.id} de {_nombre_socio(pago)} rechazado (no se recibió el dinero).')


def _resolver_arrepentimiento(request):
    solicitud = get_object_or_404(SolicitudArrepentimiento, id=request.POST.get('solicitud_id'),
                                  estado=SolicitudArrepentimiento.PENDIENTE)
    decision = request.POST.get('decision')
    respuesta = request.POST.get('respuesta', '').strip()
    if decision == 'rechazar' and not respuesta:
        messages.error(request, 'Para rechazar una solicitud tenés que escribir el motivo (se le informa al socio).')
        return

    with transaction.atomic():
        if decision == 'aceptar':
            solicitud.estado = SolicitudArrepentimiento.ACEPTADA
            pago = solicitud.pago
            if pago and pago.estado in (Pago.CONFIRMADO, Pago.PENDIENTE):
                if pago.membresia:
                    pago.membresia.activa = False
                    pago.membresia.save(update_fields=['activa'])
                pago.estado = Pago.REVOCADO
                pago.save(update_fields=['estado'])
            respuesta = respuesta or 'Solicitud aceptada. El reintegro se hace por el mismo medio de pago utilizado.'
        else:
            solicitud.estado = SolicitudArrepentimiento.RECHAZADA
        solicitud.respuesta = respuesta
        solicitud.fecha_resolucion = timezone.now()
        solicitud.resuelta_por = request.user
        solicitud.save()

    aviso = (f'Le avisamos por mail a {solicitud.email}.' if avisar_solicitud_resuelta(solicitud)
             else f'No se pudo mandar el mail: avisale a {solicitud.email}.')
    if solicitud.estado == SolicitudArrepentimiento.ACEPTADA and solicitud.pago:
        messages.success(
            request,
            f'Solicitud {solicitud.codigo} aceptada. Reintegrá ${_formatear_ars(solicitud.pago.monto)} a '
            f'{solicitud.nombre} por {solicitud.pago.get_metodo_pago_display().lower()}. {aviso}'
        )
    else:
        messages.success(request, f'Solicitud {solicitud.codigo} {solicitud.get_estado_display().lower()}. {aviso}')


# --------------------------------------------------------------------------------------------------
# PAGOS Y CAJA (compartido por el módulo admin y el módulo empleado: templates/compartido/pagos.html)
def _pagos(request, url_pagos, roles):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in roles):
        return redirect('dashboard')
    hoy = timezone.localdate()

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion in ACCIONES_COBRO:
            registrar_cobro(request, hoy)
        elif accion == 'confirmar_pago':
            _confirmar_pago(request, hoy)
        elif accion == 'rechazar_pago':
            _rechazar_pago(request)
        elif accion == 'resolver_arrepentimiento':
            _resolver_arrepentimiento(request)
        return redirect(url_pagos)

    mes_filtro = request.GET.get('mes', 'todos')
    anio_filtro = request.GET.get('anio', str(hoy.year))
    medio_filtro = request.GET.get('medio', 'todos')
    query = request.GET.get('q', '').strip()

    pagos_qs = (
        Pago.objects.exclude(estado=Pago.PENDIENTE)
        .select_related('socio__usuario', 'membresia__plan', 'plan')
        .order_by('-fecha_pago')
    )
    if query:
        pagos_qs = pagos_qs.filter(
            Q(socio__usuario__username__icontains=query)
            | Q(socio__usuario__first_name__icontains=query)
            | Q(socio__usuario__last_name__icontains=query)
        )
    if mes_filtro.isdigit():
        pagos_qs = pagos_qs.filter(fecha_pago__month=int(mes_filtro))
    if anio_filtro.isdigit():
        pagos_qs = pagos_qs.filter(fecha_pago__year=int(anio_filtro))
    if medio_filtro != 'todos':
        pagos_qs = pagos_qs.filter(metodo_pago=medio_filtro)

    # (no se usa .dates(): en MySQL sin tablas de zonas horarias devuelve None)
    rango = Pago.objects.aggregate(primero=Min('fecha_pago'), ultimo=Max('fecha_pago'))
    primer_anio = rango['primero'].year if rango['primero'] else hoy.year
    ultimo_anio = max(rango['ultimo'].year if rango['ultimo'] else hoy.year, hoy.year)
    anios = list(range(ultimo_anio, primer_anio - 1, -1))

    # Las tarjetas muestran períodos fijos hasta hoy; los filtros solo afectan a la tabla
    pagos_semana, desde_semana = _pagos_ultimos_dias(7, hoy)
    pagos_mes, desde_mes = _pagos_ultimos_dias(30, hoy)
    pagos_anio, desde_anio = _pagos_ultimos_dias(365, hoy)

    context = {
        'url_pagos': url_pagos,
        'pagos': pagos_qs,
        'pagos_pendientes': Pago.objects.pendientes().select_related('socio__usuario', 'plan').order_by('fecha_pago'),
        'solicitudes_pendientes': SolicitudArrepentimiento.objects.filter(
            estado=SolicitudArrepentimiento.PENDIENTE).select_related('pago__plan', 'pago__membresia__plan'),
        'solicitudes_resueltas': SolicitudArrepentimiento.objects.exclude(
            estado=SolicitudArrepentimiento.PENDIENTE).select_related('resuelta_por')[:10],
        'dias_arrepentimiento': DIAS_ARREPENTIMIENTO,
        'total_filtrado': _formatear_ars(_sumar(pagos_qs.filter(estado=Pago.CONFIRMADO))),
        'total_mes': _formatear_ars(_sumar(pagos_mes)),
        'total_efectivo': _formatear_ars(_sumar(pagos_mes.filter(metodo_pago='efectivo'))),
        'total_transferencia': _formatear_ars(_sumar(pagos_mes.filter(metodo_pago='transferencia'))),
        'total_semana': _formatear_ars(_sumar(pagos_semana)),
        'total_anio': _formatear_ars(_sumar(pagos_anio)),
        'cobros_mes': pagos_mes.count(),
        'cobros_semana': pagos_semana.count(),
        'cobros_anio': pagos_anio.count(),
        'desde_mes': desde_mes,
        'desde_semana': desde_semana,
        'desde_anio': desde_anio,
        'hasta': hoy,
        'meses': [(str(i), nombre) for i, nombre in enumerate(MESES, start=1)],
        'anios': [str(a) for a in anios],
        'mes_seleccionado': mes_filtro,
        'anio_seleccionado': anio_filtro,
        'medio_seleccionado': medio_filtro,
        'query': query,
        'hay_filtros': bool(query) or mes_filtro != 'todos' or medio_filtro != 'todos' or anio_filtro != str(hoy.year),
        **contexto_cobro(hoy),
    }
    return render(request, 'compartido/pagos.html', context)


# --------------------------------------------------------------------------------------------------
# BOTÓN DE ARREPENTIMIENTO (Res. 424/2020): público, sin registro previo ni trámites
def _buscar_pago(numero_recibo, dni):
    """El pago del recibo indicado, solo si pertenece al DNI informado."""
    numero = re.sub(r'\D', '', numero_recibo or '')
    if not numero:
        return None
    pago = Pago.objects.select_related('socio__usuario').filter(id=int(numero)).first()
    if not pago:
        return None
    usuario = pago.socio.usuario
    dnis = {pago.socio.dni, getattr(usuario, 'username', None), getattr(usuario, 'dni', None)}
    return pago if dni in dnis else None


def boton_arrepentimiento(request):
    user = request.user
    logueado = user.is_authenticated
    datos = {
        'nombre': user.get_full_name() if logueado else '',
        'dni': user.username if logueado and getattr(user, 'rol', '') == 'socio' else '',
        'email': user.email if logueado else '',
        'telefono': (getattr(user, 'telefono', '') or '') if logueado else '',
        'numero_recibo': request.GET.get('recibo', ''),
        'motivo': '',
    }
    errores = []

    if request.method == 'POST':
        datos = {campo: request.POST.get(campo, '').strip() for campo in datos}
        if not datos['nombre']:
            errores.append('Ingresá tu nombre y apellido.')
        if not re.fullmatch(r'\d{6,9}', datos['dni']):
            errores.append('Ingresá un DNI válido (solo números).')
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', datos['email']):
            errores.append('Ingresá un email válido para poder responderte.')
        if not errores:
            solicitud = SolicitudArrepentimiento.objects.create(
                nombre=datos['nombre'][:150],
                dni=datos['dni'],
                email=datos['email'],
                telefono=datos['telefono'][:30],
                numero_recibo=datos['numero_recibo'][:20],
                motivo=datos['motivo'],
                pago=_buscar_pago(datos['numero_recibo'], datos['dni']),
            )
            mail_enviado = avisar_solicitud_recibida(solicitud)
            return render(request, 'arrepentimiento.html', {
                'solicitud': solicitud, 'mail_enviado': mail_enviado, 'dias': DIAS_ARREPENTIMIENTO,
            })

    return render(request, 'arrepentimiento.html', {'datos': datos, 'errores': errores, 'dias': DIAS_ARREPENTIMIENTO})


@login_required
def ver_comprobante(request, pago_id):
    """Comprobante de transferencia: solo para el personal y para el socio dueño del pago."""
    pago = get_object_or_404(Pago.objects.select_related('socio__usuario'), id=pago_id)
    user = request.user
    es_personal = user.is_superuser or getattr(user, 'rol', None) in ('admin', 'recepcion', 'entrenador', 'empleado')
    if not pago.comprobante or not (es_personal or pago.socio.usuario_id == user.id):
        raise Http404('Comprobante no disponible')
    try:
        archivo = pago.comprobante.open('rb')
    except FileNotFoundError:
        raise Http404('El archivo del comprobante no existe')
    nombre = f'comprobante-REC-{pago.id}.{pago.comprobante.name.rsplit(".", 1)[-1]}'
    respuesta = FileResponse(archivo, filename=nombre)   # se abre en el navegador (no se descarga)
    respuesta['Cache-Control'] = 'private, no-store'
    return respuesta


@login_required
def admin_pagos(request):
    return _pagos(request, 'admin_pagos', ('admin',))


@login_required
def pagos_empleado(request):
    return _pagos(request, 'pagos_empleado', ('recepcion', 'entrenador', 'empleado', 'admin'))
