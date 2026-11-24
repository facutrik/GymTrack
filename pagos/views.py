from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from actividades.models import Actividad
from membresias.models import MembresiaSocio, Plan
from pagos.models import Pago
from socios.models import Socio
from usuarios.models import Usuario


def _formatear_ars(valor):
    numero = valor or 0
    return (
        f'{numero:,.2f}'.replace(',', 'X')
        .replace('.', ',')
        .replace('X', '.')
    )


@login_required
def admin_pagos(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')

    hoy = timezone.localdate()
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

    if query:
        pagos_qs = pagos_qs.filter(
            Q(socio__usuario__username__icontains=query)
            | Q(socio__usuario__first_name__icontains=query)
            | Q(socio__usuario__last_name__icontains=query)
        )
    if mes_filtro and mes_filtro != 'todos':
        pagos_qs = pagos_qs.filter(**{f'{campo_fecha}__month': int(mes_filtro)})
    if anio_filtro and anio_filtro != 'todos':
        pagos_qs = pagos_qs.filter(**{f'{campo_fecha}__year': int(anio_filtro)})
    if medio_filtro and medio_filtro != 'todos':
        pagos_qs = pagos_qs.filter(metodo_pago=medio_filtro)

    total_periodo = pagos_qs.aggregate(total=Sum('monto'))['total'] or 0
    total_efectivo = (
        pagos_qs.filter(metodo_pago='efectivo').aggregate(total=Sum('monto'))['total']
        or 0
    )
    total_transferencia = (
        pagos_qs.filter(metodo_pago='transferencia').aggregate(total=Sum('monto'))['total']
        or 0
    )

    context = {
        'pagos': pagos_qs,
        'total_periodo': _formatear_ars(total_periodo),
        'total_efectivo': _formatear_ars(total_efectivo),
        'total_transferencia': _formatear_ars(total_transferencia),
        'total_cobros': pagos_qs.count(),
        'mes_seleccionado': mes_filtro,
        'anio_seleccionado': anio_filtro,
        'medio_seleccionado': medio_filtro,
        'query': query,
    }
    return render(request, 'admin/pagos.html', context)


@login_required
def pagos_empleado(request):
    user = request.user
    if not (
        user.is_superuser
        or getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado', 'admin')
    ):
        return redirect('dashboard')

    hoy = timezone.localdate()
    campo_fecha = 'fecha_pago' if hasattr(Pago, 'fecha_pago') else 'fecha'

    if request.method == 'POST' and request.POST.get('accion') == 'cobrar_membresia_empleado':
        socio_id = request.POST.get('socio_id')
        plan_id = request.POST.get('plan_id')
        actividad_id = request.POST.get('actividad_id')
        metodo_pago = request.POST.get('metodo_pago', 'efectivo')

        socio_user = Usuario.objects.filter(id=socio_id, rol='socio').first()
        plan = Plan.objects.filter(id=plan_id).first() if plan_id else None
        actividad = Actividad.objects.filter(id=actividad_id).first() if actividad_id else None

        if not socio_user:
            messages.error(request, 'Seleccioná un socio de la lista para registrar el cobro.')
            return redirect('pagos_empleado')

        if not plan and not actividad:
            messages.error(request, 'Seleccioná un plan o una actividad para cobrar.')
            return redirect('pagos_empleado')

        socio_obj, _ = Socio.objects.get_or_create(usuario=socio_user)
        monto_total = 0
        if plan and getattr(plan, 'precio', None) is not None:
            monto_total += int(plan.precio)
        if actividad and getattr(actividad, 'precio', None) is not None:
            monto_total += int(actividad.precio)

        nueva_membresia = None
        if plan:
            duracion = getattr(plan, 'duracion_dias', 30) or 30
            MembresiaSocio.objects.filter(socio=socio_obj).update(activa=False)
            nueva_membresia = MembresiaSocio.objects.create(
                socio=socio_obj,
                plan=plan,
                fecha_inicio=hoy,
                fecha_fin=hoy + timedelta(days=duracion),
                activa=True,
            )

        pago_kwargs = {
            'socio': socio_obj,
            'monto': monto_total,
            'metodo_pago': metodo_pago,
        }
        if nueva_membresia and hasattr(Pago, 'membresia'):
            pago_kwargs['membresia'] = nueva_membresia
        if hasattr(Pago, 'fecha_pago'):
            pago_kwargs['fecha_pago'] = timezone.now()
        elif hasattr(Pago, 'fecha'):
            pago_kwargs['fecha'] = hoy

        Pago.objects.create(**pago_kwargs)

        if hasattr(socio_obj, 'estado_cuenta'):
            socio_obj.estado_cuenta = 'VERDE'
            socio_obj.save()

        nombre_socio = f'{socio_user.first_name} {socio_user.last_name}'.strip() or socio_user.username
        messages.success(
            request,
            f'Cobro de ${monto_total} ({metodo_pago}) registrado para {nombre_socio}.',
        )
        return redirect('pagos_empleado')

    socios_usuarios = Usuario.objects.filter(rol='socio', is_active=True).order_by(
        'first_name', 'last_name'
    )
    socios_para_cobro = []
    for s in socios_usuarios:
        perfil = Socio.objects.filter(usuario=s).first()
        al_dia = False
        vence_str = ''
        if perfil:
            membresia_vigente = (
                MembresiaSocio.objects.filter(socio=perfil, activa=True)
                .order_by('-fecha_fin')
                .first()
            )
            if membresia_vigente and membresia_vigente.fecha_fin >= hoy:
                al_dia = True
                vence_str = membresia_vigente.fecha_fin.strftime('%d/%m/%Y')
        socios_para_cobro.append({
            'id': s.id,
            'nombre': f'{s.first_name} {s.last_name}'.strip() or s.username,
            'dni': s.username,
            'al_dia': al_dia,
            'vence': vence_str,
        })

    ultimos_cobros = Pago.objects.select_related('socio__usuario', 'membresia__plan').order_by(
        f'-{campo_fecha}'
    )[:30]

    context = {
        'socios_para_cobro': socios_para_cobro,
        'planes_disponibles': Plan.objects.all().order_by('precio'),
        'actividades_disponibles': Actividad.objects.all().order_by('nombre'),
        'ultimos_cobros': ultimos_cobros,
    }
    return render(request, 'empleado/pagos.html', context)