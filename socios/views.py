from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from usuarios.models import Usuario

try:
    from socios.models import Socio
except ImportError:
    Socio = None


# ==========================================================
# 👥 1. GESTIÓN DE SOCIOS PARA EL ADMINISTRADOR
# ==========================================================
@login_required
def admin_socios(request):
    """Listado general y gestión de socios desde el panel del Administrador"""
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # Alta de nuevo socio
        if accion == 'alta':
            dni = request.POST.get('dni', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            email = request.POST.get('email', '').strip()
            telefono = request.POST.get('telefono', '').strip()
            password = request.POST.get('password', '').strip() or '123'

            if Usuario.objects.filter(username=dni).exists():
                messages.error(request, f'Ya existe un socio registrado con el DNI {dni}.')
            else:
                nuevo = Usuario.objects.create_user(
                    username=dni,
                    email=email,
                    password=password,
                    first_name=nombre,
                    last_name=apellido
                )
                nuevo.rol = 'socio'
                if hasattr(nuevo, 'telefono'):
                    nuevo.telefono = telefono
                nuevo.save()

                if Socio:
                    Socio.objects.get_or_create(usuario=nuevo, defaults={'estado_cuenta': 'VERDE'})

                messages.success(request, f'Socio {nombre} {apellido} registrado con éxito.')
            return redirect('admin_socios')

        # Editar datos de socio existente
        elif accion == 'editar':
            socio_id = request.POST.get('socio_id')
            socio = get_object_or_404(Usuario, id=socio_id, rol='socio')
            socio.first_name = request.POST.get('nombre', '').strip()
            socio.last_name = request.POST.get('apellido', '').strip()
            socio.email = request.POST.get('email', '').strip()
            if hasattr(socio, 'telefono'):
                socio.telefono = request.POST.get('telefono', '').strip()
            nueva_pass = request.POST.get('password', '').strip()
            if nueva_pass:
                socio.set_password(nueva_pass)
            socio.save()
            messages.success(request, f'Datos de {socio.get_full_name()} actualizados.')
            return redirect('admin_socios')

        # Eliminar socio permanentemente
        elif accion == 'eliminar':
            socio_id = request.POST.get('socio_id')
            socio = get_object_or_404(Usuario, id=socio_id, rol='socio')
            nombre_completo = socio.get_full_name()
            socio.delete()
            messages.success(request, f'Socio {nombre_completo} eliminado permanentemente.')
            return redirect('admin_socios')

        # Dar de baja o reactivar (toggle is_active)
        elif accion == 'toggle_baja':
            socio_id = request.POST.get('socio_id')
            socio = get_object_or_404(Usuario, id=socio_id, rol='socio')
            socio.is_active = not socio.is_active
            socio.save()
            estado = "activo" if socio.is_active else "dado de baja"
            messages.success(request, f'El socio {socio.get_full_name()} ahora está {estado}.')
            return redirect('admin_socios')

    # Búsqueda y listado
    query = request.GET.get('q', '').strip()
    socios_qs = Usuario.objects.filter(rol='socio').order_by('-date_joined')

    if query:
        socios_qs = socios_qs.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    # Armado del contexto compatible con template admin/socios.html (item.usuario)
    lista_socios = []
    for u in socios_qs:
        soc_obj = getattr(u, 'perfil_socio', None)
        if not soc_obj and Socio:
            soc_obj = Socio.objects.filter(usuario=u).first()

        estado_cuota = getattr(soc_obj, 'estado_cuenta', getattr(u, 'estado_cuenta', 'VERDE'))
        lista_socios.append({
            'usuario': u,
            'socio': soc_obj,
            'estado_cuota': str(estado_cuota).upper(),
            'medio_pago': getattr(soc_obj, 'medio_pago', 'efectivo'),
        })

    context = {
        'socios': lista_socios,
        'query': query,
        'total_socios': socios_qs.count(),
    }
    return render(request, 'admin/socios.html', context)


# ==========================================================
# 📋 2. PADRÓN DE SOCIOS PARA EMPLEADO / RECEPCIÓN
# ==========================================================
@login_required
def padron_socios_empleado(request):
    """Padrón de socios para el mostrador de recepción"""
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado', 'admin')):
        return redirect('dashboard')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'alta':
            dni = request.POST.get('dni', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            email = request.POST.get('email', '').strip()
            telefono = request.POST.get('telefono', '').strip()

            if Usuario.objects.filter(username=dni).exists():
                messages.error(request, f'Ya existe un socio registrado con el DNI {dni}.')
            else:
                nuevo = Usuario.objects.create_user(
                    username=dni,
                    email=email,
                    password='123',
                    first_name=nombre,
                    last_name=apellido
                )
                nuevo.rol = 'socio'
                if hasattr(nuevo, 'telefono'):
                    nuevo.telefono = telefono
                nuevo.save()

                if Socio:
                    Socio.objects.get_or_create(usuario=nuevo, defaults={'estado_cuenta': 'VERDE'})

                messages.success(request, f'Socio {nombre} {apellido} registrado con éxito.')
            return redirect('padron_socios_empleado')

        elif accion == 'editar':
            socio_id = request.POST.get('socio_id')
            socio = get_object_or_404(Usuario, id=socio_id, rol='socio')
            socio.first_name = request.POST.get('nombre', '').strip()
            socio.last_name = request.POST.get('apellido', '').strip()
            socio.email = request.POST.get('email', '').strip()
            if hasattr(socio, 'telefono'):
                socio.telefono = request.POST.get('telefono', '').strip()
            socio.save()
            messages.success(request, f'Datos de {socio.get_full_name()} actualizados.')
            return redirect('padron_socios_empleado')

        elif accion == 'toggle_baja':
            socio_id = request.POST.get('socio_id')
            socio = get_object_or_404(Usuario, id=socio_id, rol='socio')
            socio.is_active = not socio.is_active
            socio.save()
            estado = "activo" if socio.is_active else "dado de baja"
            messages.success(request, f'El socio {socio.get_full_name()} ahora está {estado}.')
            return redirect('padron_socios_empleado')

    query = request.GET.get('q', '').strip()
    socios = Usuario.objects.filter(rol='socio').order_by('-date_joined')

    if query:
        socios = socios.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    context = {
        'socios': socios,
        'query': query,
        'total_socios': socios.count(),
    }
    return render(request, 'empleado/socios.html', context)