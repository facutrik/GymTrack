from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.utils import timezone
from pagos.models import Pago

@login_required
def admin_pagos(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')

    hoy = timezone.localdate()
    mes_actual = hoy.month
    anio_actual = hoy.year

    mes_filtro = request.GET.get('mes', str(mes_actual))
    anio_filtro = request.GET.get('anio', str(anio_actual))
    metodo_filtro = request.GET.get('medio', 'todos')
    query = request.GET.get('q', '').strip()

    pagos = Pago.objects.all().order_by('-fecha_pago')

    if mes_filtro.isdigit():
        pagos = pagos.filter(fecha_pago__month=int(mes_filtro))
    if anio_filtro.isdigit():
        pagos = pagos.filter(fecha_pago__year=int(anio_filtro))

    if metodo_filtro != 'todos':
        pagos = pagos.filter(metodo_pago=metodo_filtro)

    if query:
        pagos = pagos.filter(
            Q(socio__usuario__username__icontains=query) |
            Q(socio__usuario__first_name__icontains=query) |
            Q(socio__usuario__last_name__icontains=query)
        )

    total_recaudado = pagos.aggregate(total=Sum('monto'))['total'] or 0
    total_efectivo = pagos.filter(metodo_pago='efectivo').aggregate(total=Sum('monto'))['total'] or 0
    total_transferencia = pagos.filter(metodo_pago='transferencia').aggregate(total=Sum('monto'))['total'] or 0
    total_debito = pagos.filter(metodo_pago='debito').aggregate(total=Sum('monto'))['total'] or 0

    context = {
        'pagos': pagos,
        'total_recaudado': total_recaudado,
        'total_efectivo': total_efectivo,
        'total_transferencia': total_transferencia,
        'total_debito': total_debito,
        'mes_filtro': mes_filtro,
        'anio_filtro': anio_filtro,
        'medio_filtro': metodo_filtro,
        'query': query,
        'cantidad_cobros': pagos.count(),
    }
    return render(request, 'admin/pagos.html', context)
