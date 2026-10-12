# socios/views.py
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from django.utils import timezone
from django.contrib import messages
from usuarios.models import Usuario

# Importamos membresía si ya tenés el modelo para chequear el vencimiento
try:
    from membresias.models import MembresiaSocio
except ImportError:
    MembresiaSocio = None


@login_required
def admin_socios(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')

    hoy = timezone.localdate()
    limite_3_meses = hoy - timedelta(days=90)

    # 1. PROCESAR ACCIONES POST (Alta o Baja Manual)
    if request.method == 'POST':
        accion = request.POST.get('accion')

        # Acción: Dar de baja o reactivar manualmente
        if accion == 'toggle_baja':
            socio_id = request.POST.get('socio_id')
            socio_a_cambiar = get_object_or_404(Usuario, id=socio_id, rol='socio')
            
            # Cambiamos su estado activo
            socio_a_cambiar.is_active = not socio_a_cambiar.is_active
            socio_a_cambiar.save()

            estado_str = "activo" if socio_a_cambiar.is_active else "dado de baja"
            messages.success(request, f"El socio {socio_a_cambiar.username} fue marcado como {estado_str}.")
            return redirect('admin_socios')

        # Acción: Alta de nuevo socio
        elif accion == 'alta':
            dni = request.POST.get('dni', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            email = request.POST.get('email', '').strip()
            telefono = request.POST.get('telefono', '').strip()
            password = request.POST.get('password', '').strip() or '123'

            if Usuario.objects.filter(username=dni).exists():
                messages.error(request, f'Ya existe un usuario con el DNI {dni}.')
            else:
                nuevo_socio = Usuario.objects.create_user(
                    username=dni,
                    email=email,
                    password=password,
                    first_name=nombre,
                    last_name=apellido
                )
                nuevo_socio.rol = 'socio'
                nuevo_socio.is_active = True
                if hasattr(nuevo_socio, 'dni'):
                    nuevo_socio.dni = dni
                if hasattr(nuevo_socio, 'telefono'):
                    nuevo_socio.telefono = telefono
                nuevo_socio.save()

                messages.success(request, f'Socio {nombre} {apellido} registrado con éxito.')
                return redirect('admin_socios')

    # 2. FILTRADO Y BÚSQUEDA
    query = request.GET.get('q', '').strip()
    filtro_estado = request.GET.get('estado', 'todos') # todos, activos, inactivos

    socios = Usuario.objects.filter(rol='socio').order_by('-date_joined')

    # Búsqueda directa por DNI, Nombre o Apellido
    if query:
        socios = socios.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    # Filtro por estado activo/inactivo
    if filtro_estado == 'activos':
        socios = socios.filter(is_active=True)
    elif filtro_estado == 'inactivos':
        socios = socios.filter(is_active=False)

    # 3. REGLA AUTOMÁTICA DE BAJA A LOS 3 MESES (90 DÍAS SIN PAGAR)
    # Si existe el historial de membresías, revisamos quién superó los 90 días vencido
    socios_lista = []
    for s in socios:
        ultimo_vencimiento = None
        estado_cuota = "VERDE"
        
        if MembresiaSocio:
            # Buscamos su último vencimiento registrado
            ultima_memb = MembresiaSocio.objects.filter(socio__usuario=s).aggregate(Max('fecha_fin'))['fecha_fin__max']
            if ultima_memb:
                ultimo_vencimiento = ultima_memb
                if ultima_memb < hoy:
                    estado_cuota = "ROJO"
                    # Si pasaron más de 90 días desde que venció y seguía activo, se da de baja solo
                    if ultima_memb < limite_3_meses and s.is_active:
                        s.is_active = False
                        s.save()
            else:
                # Si nunca pagó y su fecha de alta supera los 90 días
                if s.date_joined.date() < limite_3_meses and s.is_active:
                    s.is_active = False
                    s.save()
                estado_cuota = "ROJO"

        socios_lista.append({
            'usuario': s,
            'estado_cuota': estado_cuota,
            'ultimo_vencimiento': ultimo_vencimiento
        })

    context = {
        'socios': socios_lista,
        'query': query,
        'filtro_estado': filtro_estado,
        'total_socios': len(socios_lista),
    }
    return render(request, 'admin/socios.html', context)