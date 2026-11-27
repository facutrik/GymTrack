"""
Mails del Botón de Arrepentimiento. Si el mail no se puede mandar, la solicitud igual queda
registrada (el código se muestra en pantalla), así que un error de correo nunca corta el trámite.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def _enviar(asunto, cuerpo, destinatarios):
    destinatarios = [d for d in destinatarios if d]
    if not destinatarios:
        return False
    try:
        send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, destinatarios, fail_silently=False)
        return True
    except Exception:
        logger.exception('No se pudo enviar el mail "%s" a %s', asunto, destinatarios)
        return False


def _gimnasio():
    return getattr(settings, 'DATOS_GIMNASIO', {})


def _detalle_pago(solicitud):
    if solicitud.pago:
        p = solicitud.pago
        return f'Pago: #REC-{p.id} - {p.concepto} - ${p.monto:,.0f} ({p.get_metodo_pago_display()})'.replace(',', '.')
    if solicitud.numero_recibo:
        return f'Recibo informado: {solicitud.numero_recibo} (no coincide con el DNI, hay que revisarlo)'
    return 'Recibo: no informado (buscarlo por DNI)'


def avisar_solicitud_recibida(solicitud):
    """Le manda el código al socio y avisa al gimnasio. Devuelve True si el socio recibió el mail."""
    g = _gimnasio()
    fecha = timezone.localtime(solicitud.fecha_solicitud).strftime('%d/%m/%Y %H:%M')
    al_socio = _enviar(
        f'Recibimos tu solicitud de arrepentimiento ({solicitud.codigo})',
        f'Hola {solicitud.nombre}:\n\n'
        f'Recibimos tu solicitud de revocación (Botón de Arrepentimiento) el {fecha} hs.\n\n'
        f'Código de solicitud: {solicitud.codigo}\n'
        f'{_detalle_pago(solicitud)}\n\n'
        'Si corresponde, damos de baja el plan y te reintegramos el importe por el mismo medio de pago '
        'que usaste. Te vamos a avisar por este medio cuando la resolvamos.\n\n'
        f'Ante cualquier consulta respondé este correo indicando el código.\n\n'
        f'{g.get("razon_social", "")} · CUIT {g.get("cuit", "")}\n{g.get("domicilio", "")}',
        [solicitud.email],
    )
    _enviar(
        f'[GymTrack] Nueva solicitud de arrepentimiento {solicitud.codigo}',
        f'Entró una solicitud por el Botón de Arrepentimiento.\n\n'
        f'Código: {solicitud.codigo}\nFecha: {fecha} hs\n'
        f'Nombre: {solicitud.nombre}\nDNI: {solicitud.dni}\nEmail: {solicitud.email}\n'
        f'Teléfono: {solicitud.telefono or "-"}\n{_detalle_pago(solicitud)}\n'
        f'Comentario: {solicitud.motivo or "-"}\n\n'
        'Resolvela desde Pagos y Caja en GymTrack.',
        [g.get('email') or settings.EMAIL_HOST_USER],
    )
    return al_socio


def avisar_solicitud_resuelta(solicitud):
    g = _gimnasio()
    if solicitud.estado == solicitud.ACEPTADA:
        resultado = 'fue ACEPTADA. Dimos de baja el plan y vamos a reintegrarte el importe por el mismo medio de pago que usaste.'
    else:
        resultado = 'fue RECHAZADA.'
    return _enviar(
        f'Tu solicitud de arrepentimiento {solicitud.codigo} fue {solicitud.get_estado_display().lower()}',
        f'Hola {solicitud.nombre}:\n\n'
        f'Tu solicitud {solicitud.codigo} {resultado}\n\n'
        f'{("Detalle: " + solicitud.respuesta) if solicitud.respuesta else ""}\n\n'
        f'Si tenés dudas, respondé este correo o acercate a recepción.\n\n'
        f'{g.get("razon_social", "")} · {g.get("telefono", "")}',
        [solicitud.email],
    )
