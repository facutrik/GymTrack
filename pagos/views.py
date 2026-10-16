from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from pagos.models import Pago


@login_required
def admin_pagos(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')

    hoy = timezone.localdate()

    # Por defecto 'todos' para ver toda la caja histórica o el mes actual
    mes_filtro = request.GET.get('mes', 'todos')
    anio_filtro = request.GET.get('anio', str(hoy.year))
    medio_filtro = request.GET.get('medio', 'todos')
    query = request.GET.get('q', '').strip()

    campo_fecha = 'fecha_pago' if hasattr(Pago, 'fecha_pago') else 'fecha'

    pagos_qs = (
        Pago.objects.select_related('socio__usuario', 'membresia__plan')
        .all()
        .order_by(f'-{campo_fecha}')
    )

    # Búsqueda por DNI o Nombre
    if query:
        pagos_qs = pagos_qs.filter(
            Q(socio__usuario__username__icontains=query)
            | Q(socio__usuario__first_name__icontains=query)
            | Q(socio__usuario__last_name__icontains=query)
        )

    # Filtro de Mes
    if mes_filtro and mes_filtro != 'todos':
        pagos_qs = pagos_qs.filter(**{f'{campo_fecha}__month': int(mes_filtro)})

    # Filtro de Año
    if anio_filtro and anio_filtro != 'todos':
        pagos_qs = pagos_qs.filter(**{f'{campo_fecha}__year': int(anio_filtro)})

    # Filtro de Medio (Efectivo / Transferencia)
    if medio_filtro and medio_filtro != 'todos':
        pagos_qs = pagos_qs.filter(metodo_pago=medio_filtro)

    # Cálculos de Totales
    total_periodo = pagos_qs.aggregate(total=Sum('monto'))['total'] or 0
    total_efectivo = (
        pagos_qs.filter(metodo_pago='efectivo').aggregate(total=Sum('monto'))[
            'total'
        ]
        or 0
    )
    total_transferencia = (
        pagos_qs.filter(metodo_pago='transferencia').aggregate(
            total=Sum('monto')
        )['total']
        or 0
    )

    context = {
        'pagos': pagos_qs,
        'total_periodo': f'{total_periodo:,.2f}'.replace(',', 'X')
        .replace('.', ',')
        .replace('X', '.'),
        'total_efectivo': f'{total_efectivo:,.2f}'.replace(',', 'X')
        .replace('.', ',')
        .replace('X', '.'),
        'total_transferencia': f'{total_transferencia:,.2f}'.replace(',', 'X')
        .replace('.', ',')
        .replace('X', '.'),
        'total_cobros': pagos_qs.count(),
        'mes_seleccionado': mes_filtro,
        'anio_seleccionado': anio_filtro,
        'medio_seleccionado': medio_filtro,
        'query': query,
    }
    return render(request, 'admin/pagos.html', context)
