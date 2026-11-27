import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from membresias.models import MembresiaSocio, Plan
from socios.models import Socio

# Art. 34 Ley 24.240 y art. 1110 del Código Civil y Comercial: 10 días corridos para revocar
DIAS_ARREPENTIMIENTO = 10


def _ruta_comprobante(pago, archivo):
    """comprobantes/2026/11/<aleatorio>.<ext>: el nombre no revela de quién es el comprobante."""
    extension = archivo.rsplit('.', 1)[-1].lower() if '.' in archivo else 'bin'
    return f"comprobantes/{timezone.localdate():%Y/%m}/{secrets.token_hex(12)}.{extension}"


class PagoQuerySet(models.QuerySet):
    def confirmados(self):
        """Los que cuentan como ingreso (los pendientes y revocados no)."""
        return self.filter(estado=Pago.CONFIRMADO)

    def pendientes(self):
        return self.filter(estado=Pago.PENDIENTE)


class Pago(models.Model):
    METODOS = (
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia MP'),
    )
    CONFIRMADO, PENDIENTE, RECHAZADO, REVOCADO = 'confirmado', 'pendiente', 'rechazado', 'revocado'
    ESTADOS = (
        (CONFIRMADO, 'Confirmado'),
        (PENDIENTE, 'Pendiente de confirmación'),
        (RECHAZADO, 'Rechazado'),
        (REVOCADO, 'Revocado (arrepentimiento)'),
    )
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
    membresia = models.ForeignKey(MembresiaSocio, on_delete=models.SET_NULL, null=True, blank=True)
    # Plan que pidió el socio al pagar desde la web: la membresía se activa recién al confirmar el pago
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=20, choices=METODOS, default='efectivo')
    estado = models.CharField(max_length=12, choices=ESTADOS, default=CONFIRMADO)
    # Transferencias hechas por el socio desde la web: recepción las verifica con esto antes de confirmar.
    # Los archivos NO son públicos: solo se ven con la vista ver_comprobante (personal o el mismo socio).
    comprobante = models.FileField(upload_to=_ruta_comprobante, blank=True)
    referencia = models.CharField('N.º de operación', max_length=60, blank=True)

    objects = PagoQuerySet.as_manager()

    @property
    def concepto(self):
        plan = self.membresia.plan if self.membresia else self.plan
        return plan.nombre if plan else 'Cuota mensual'

    @property
    def puede_arrepentirse(self):
        """Dentro de los 10 días corridos desde el pago, y si no fue revocado ni rechazado."""
        limite = timezone.localtime(self.fecha_pago).date() + timedelta(days=DIAS_ARREPENTIMIENTO)
        return self.estado in (self.CONFIRMADO, self.PENDIENTE) and timezone.localdate() <= limite

    def __str__(self):
        return f"Pago de {self.socio} - ${self.monto} ({self.fecha_pago.strftime('%d/%m/%Y')})"


def _codigo_arrepentimiento():
    return 'ARR-' + timezone.localdate().strftime('%Y%m%d') + '-' + secrets.token_hex(3).upper()


class SolicitudArrepentimiento(models.Model):
    """Pedido de revocación hecho desde el Botón de Arrepentimiento (Res. 424/2020)."""
    PENDIENTE, ACEPTADA, RECHAZADA = 'pendiente', 'aceptada', 'rechazada'
    ESTADOS = (
        (PENDIENTE, 'Pendiente'),
        (ACEPTADA, 'Aceptada'),
        (RECHAZADA, 'Rechazada'),
    )
    codigo = models.CharField(max_length=20, unique=True, default=_codigo_arrepentimiento, editable=False)
    nombre = models.CharField(max_length=150)
    dni = models.CharField(max_length=20)
    email = models.EmailField()
    telefono = models.CharField(max_length=30, blank=True)
    numero_recibo = models.CharField(max_length=20, blank=True)
    motivo = models.TextField(blank=True)
    pago = models.ForeignKey(Pago, on_delete=models.SET_NULL, null=True, blank=True, related_name='arrepentimientos')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default=PENDIENTE)
    respuesta = models.TextField(blank=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    resuelta_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-fecha_solicitud']

    @property
    def dentro_de_plazo(self):
        if not self.pago:
            return None
        pagado = timezone.localtime(self.pago.fecha_pago).date()
        pedido = timezone.localtime(self.fecha_solicitud).date()
        return (pedido - pagado).days <= DIAS_ARREPENTIMIENTO

    def __str__(self):
        return f'{self.codigo} - {self.nombre} ({self.get_estado_display()})'
