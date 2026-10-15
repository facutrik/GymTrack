# socios/views.py
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from django.utils import timezone
from django.contrib import messages

from usuarios.models import Usuario
from pagos.models import Pago

try:
    from membresias.models import MembresiaSocio
except ImportError:
    MembresiaSocio = None

from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from usuarios.models import Usuario

# ==========================================================
# 🛡️ 1. MÓDULO ADMINISTRADOR: GESTIÓN DE SOCIOS
# ==========================================================
@login_required
def admin_socios(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')

    hoy = timezone.localdate()
    limite_3_meses = hoy - timedelta(days=90)

    # 1. PROCESAR ACCIONES POST (Alta, Editar, Eliminar, Baja Manual)
    if request.method == 'POST':
        accion = request.POST.get('accion')

        # Acción: ALTA
        if accion == 'alta':
    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'toggle_baja':
            socio_id = request.POST.get('socio_id')
            socio = get_object_or_404(Usuario, id=socio_id, rol='socio')
            socio.is_active = not socio.is_active
            socio.save()
            estado = "activo" if socio.is_active else "dado de baja"
            messages.success(request, f'Socio {socio.username} ahora está {estado}.')
            return redirect('admin_socios')

        elif accion == 'alta':
            dni = request.POST.get('dni', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip() or '123'

            if Usuario.objects.filter(username=dni).exists():
                messages.error(request, f'Ya existe un usuario con el DNI {dni}.')
            else:
                nuevo_socio = Usuario.objects.create_user(
                    username=dni, email=email, password=password,
                    first_name=nombre, last_name=apellido
                )
                nuevo_socio.rol = 'socio'
                nuevo_socio.is_active = True
                nuevo_socio.save()
                messages.success(request, f'Socio {nombre} {apellido} registrado con éxito.')
            return redirect('admin_socios')

        # Acción: EDITAR
        elif accion == 'editar':
            socio_id = request.POST.get('socio_id')
            socio_editar = get_object_or_404(Usuario, id=socio_id, rol='socio')
            
            socio_editar.first_name = request.POST.get('nombre', '').strip()
            socio_editar.last_name = request.POST.get('apellido', '').strip()
            socio_editar.email = request.POST.get('email', '').strip()
            
            # Actualizar contraseña solo si se ingresó una nueva
            nueva_password = request.POST.get('password', '').strip()
            if nueva_password:
                socio_editar.set_password(nueva_password)
                
            socio_editar.save()
            messages.success(request, f'Socio {socio_editar.first_name} actualizado.')
            return redirect('admin_socios')

        # Acción: ELIMINAR (Borrado físico)
        elif accion == 'eliminar':
            socio_id = request.POST.get('socio_id')
            socio_eliminar = get_object_or_404(Usuario, id=socio_id, rol='socio')
            nombre_eliminado = f"{socio_eliminar.first_name} {socio_eliminar.last_name}"
            socio_eliminar.delete()
            messages.success(request, f'Socio {nombre_eliminado} eliminado del sistema.')
            return redirect('admin_socios')

        # Acción: TOGGLE BAJA (Borrado lógico)
                messages.error(request, f'Ya existe un socio con DNI {dni}.')
            else:
                nuevo = Usuario.objects.create_user(
                    username=dni,
                    email=email,
                    password=password,
                    first_name=nombre,
                    last_name=apellido
                )
                nuevo.rol = 'socio'
                nuevo.is_active = True
                if hasattr(nuevo, 'dni'):
                    nuevo.dni = dni
                nuevo.save()
                messages.success(request, f'Socio {nombre} {apellido} registrado con éxito.')
            return redirect('admin_socios')

    query = request.GET.get('q', '').strip()
    filtro_estado = request.GET.get('estado', 'todos')

    socios_qs = Usuario.objects.filter(rol='socio').order_by('-date_joined')

    if query:
        socios_qs = socios_qs.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    if filtro_estado == 'activos':
        socios_qs = socios_qs.filter(is_active=True)
    elif filtro_estado == 'inactivos':
        socios_qs = socios_qs.filter(is_active=False)

    # Armamos la estructura requerida por el template templates/admin/socios.html
    socios_lista = []
    for s in socios_qs:
        # Baja automática si tiene más de 90 días de antigüedad sin regularizar
        if s.date_joined.date() < limite_3_meses and s.is_active:
            s.is_active = False
            s.save()

        estado_cuota = getattr(s, 'estado_cuenta', 'VERDE')

        socios_lista.append({
            'usuario': s,
            'estado_cuota': estado_cuota,
            'ultimo_vencimiento': None,
            'medio_pago': 'Efectivo / Transferencia',
        })

    context = {
        'socios': socios_lista,
        'query': query,
        'filtro_estado': filtro_estado,
        'total_socios': len(socios_lista),
    }
    return render(request, 'admin/socios.html', context)


# ==========================================================
# 📋 2. MÓDULO EMPLEADO: PADRÓN OPERATIVO Y CRUD MOSTRADOR
# ==========================================================
@login_required
def padron_socios_empleado(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado', 'admin')):
        return redirect('dashboard')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # ALTA DE SOCIO
        if accion == 'alta':
            dni = request.POST.get('dni', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            email = request.POST.get('email', '').strip()
            telefono = request.POST.get('telefono', '').strip()

            if Usuario.objects.filter(username=dni).exists():
                messages.error(request, f'El DNI {dni} ya está registrado.')
            else:
                nuevo = Usuario.objects.create_user(
                    username=dni,
                    email=email,
                    password='123',
                    first_name=nombre,
                    last_name=apellido
                )
                nuevo.rol = 'socio'
                if hasattr(nuevo, 'dni'):
                    nuevo.dni = dni
                if hasattr(nuevo, 'telefono'):
                    nuevo.telefono = telefono
                nuevo.save()
                messages.success(request, f'Socio {nombre} {apellido} registrado con éxito.')
            return redirect('padron_socios_empleado')

        # EDITAR SOCIO
        elif accion == 'editar':
            socio_id = request.POST.get('socio_id')
            socio = get_object_or_404(Usuario, id=socio_id, rol='socio')
            socio.first_name = request.POST.get('nombre', '').strip()
            socio.last_name = request.POST.get('apellido', '').strip()
            socio.email = request.POST.get('email', '').strip()
            if hasattr(socio, 'telefono'):
                socio.telefono = request.POST.get('telefono', '').strip()
            socio.save()
            messages.success(request, f'Datos de {socio.first_name} actualizados.')
            return redirect('padron_socios_empleado')

        # DAR DE BAJA / REACTIVAR (Baja lógica)
        elif accion == 'toggle_baja':
            socio_id = request.POST.get('socio_id')
            socio = get_object_or_404(Usuario, id=socio_id, rol='socio')
            socio.is_active = not socio.is_active
            socio.save()
            return redirect('admin_socios')


    # 2. BÚSQUEDA Y LISTADO
            estado = "activo" if socio.is_active else "dado de baja"
            messages.success(request, f'El socio {socio.first_name} {socio.last_name} ahora está {estado}.')
            return redirect('padron_socios_empleado')

    # Búsqueda y listado para la plantilla templates/empleado/soci.html
    query = request.GET.get('q', '').strip()
    socios = Usuario.objects.filter(rol='socio').order_by('-date_joined')

    if query:
        socios = socios.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    # 3. ENRIQUECER DATOS (Estado de cuota y último medio de pago)
    socios_lista = []
    for s in socios:
        estado_cuota = "VERDE"
        ultimo_vencimiento = None
        
        # Analizar membresía
        if MembresiaSocio:
            ultima_memb = MembresiaSocio.objects.filter(socio__usuario=s).aggregate(Max('fecha_fin'))['fecha_fin__max']
            if ultima_memb:
                ultimo_vencimiento = ultima_memb
                if ultima_memb < hoy:
                    estado_cuota = "ROJO"
                    # Baja automática a los 90 días
                    if ultima_memb < limite_3_meses and s.is_active:
                        s.is_active = False
                        s.save()
            else:
                # Si nunca pagó y su fecha de alta supera los 90 días
                if s.date_joined.date() < limite_3_meses and s.is_active:
                    s.is_active = False
                    s.save()
                estado_cuota = "ROJO"

        # Buscar el último medio de pago
        ultimo_pago = Pago.objects.filter(socio__usuario=s).order_by('-fecha_pago').first()
        medio_pago = ultimo_pago.metodo_pago if ultimo_pago else "Sin registros"

        socios_lista.append({
            'usuario': s,
            'estado_cuota': estado_cuota,
            'ultimo_vencimiento': ultimo_vencimiento,
            'medio_pago': medio_pago,
        })

    context = {
        'socios': socios_lista,
        'query': query,
        'total_socios': len(socios_lista),
    }
    return render(request, 'admin/socios.html', context)    
            Q(last_name__icontains=query)
        )

    context = {
        'socios': socios,
        'query': query,
        'total_socios': socios.count(),
    }
    return render(request, 'empleado/socios.html', context)
