from django.db import models
from socios.models import Socio
from membresias.models import MembresiaSocio

class Pago(models.Model):
    METODOS = (
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia MP'),
    )
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
    membresia = models.ForeignKey(MembresiaSocio, on_delete=models.SET_NULL, null=True, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=20, choices=METODOS, default='efectivo')

    def __str__(self):
        return f"Pago de {self.socio} - ${self.monto} ({self.fecha_pago.strftime('%d/%m/%Y')})"