from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Q
from pagos.models import Pago

@login_required
def admin_pagos(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')

    hoy = timezone.localdate()
    mes_filtro = request.GET.get('mes', str(hoy.month))
    anio_filtro = request.GET.get('anio', str(hoy.year))
    medio_filtro = request.GET.get('medio', 'todos')
    query = request.GET.get('q', '').strip()

    # Determinar el nombre exacto del campo de fecha en el modelo Pago
    campo_fecha = 'fecha_pago' if hasattr(Pago, 'fecha_pago') else 'fecha'

    # Consulta base con select_related para traer socio, usuario y plan
    pagos_qs = Pago.objects.select_related('socio__usuario', 'membresia__plan').all().order_by(f'-{campo_fecha}')

    # Filtro por búsqueda de DNI o Nombre si se ingresó texto
    if query:
        pagos_qs = pagos_qs.filter(
            Q(socio__usuario__username__icontains=query) |
            Q(socio__usuario__first_name__icontains=query) |
            Q(socio__usuario__last_name__icontains=query)
        )

    # Filtro por mes y año (si no se selecciona 'todos')
    if mes_filtro and mes_filtro != 'todos':
        pagos_qs = pagos_qs.filter(**{f"{campo_fecha}__month": int(mes_filtro)})
    if anio_filtro and anio_filtro != 'todos':
        pagos_qs = pagos_qs.filter(**{f"{campo_fecha}__year": int(anio_filtro)})

    # Filtro por medio de pago
    if medio_filtro and medio_filtro != 'todos':
        pagos_qs = pagos_qs.filter(metodo_pago=medio_filtro)

    # Totales monetarios calculados sobre el queryset filtrado
    total_periodo = pagos_qs.aggregate(total=Sum('monto'))['total'] or 0
    total_efectivo = pagos_qs.filter(metodo_pago='efectivo').aggregate(total=Sum('monto'))['total'] or 0
    total_transferencia = pagos_qs.filter(metodo_pago='transferencia').aggregate(total=Sum('monto'))['total'] or 0
    total_debito = pagos_qs.filter(metodo_pago__in=['tarjeta', 'debito']).aggregate(total=Sum('monto'))['total'] or 0

    context = {
        'pagos': pagos_qs,
        'total_periodo': total_periodo,
        'total_efectivo': total_efectivo,
        'total_transferencia': total_transferencia,
        'total_debito': total_debito,
        'total_cobros': pagos_qs.count(),
        'mes_seleccionado': int(mes_filtro) if mes_filtro.isdigit() else hoy.month,
        'anio_seleccionado': int(anio_filtro) if anio_filtro.isdigit() else hoy.year,
        'medio_seleccionado': medio_filtro,
        'query': query,
    }
    return render(request, 'admin/pagos.html', context)
