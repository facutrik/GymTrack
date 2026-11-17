from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from usuarios.models import Usuario
from socios.models import Socio


try:
    from membresias.models import MembresiaSocio
except ImportError:
    MembresiaSocio = None
# ==========================================================
# 🛡️ 1. MÓDULO ADMINISTRADOR: GESTIÓN DE SOCIOS
# ==========================================================
@login_required
def admin_socios(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in ('admin', 'recepcion', 'empleado', 'entrenador')):
        return redirect('dashboard')

    hoy = timezone.localdate()
    limite_3_meses = hoy - timedelta(days=90)

    # 1. PROCESAR ACCIONES POST (Alta o Baja / Reactivación)
    if request.method == 'POST':
        accion = request.POST.get('accion')

        # TOGGLE BAJA / ALTA LÓGICA
        if accion == 'toggle_baja':
            socio_id = request.POST.get('socio_id')
            socio_user = get_object_or_404(Usuario, id=socio_id, rol='socio')
            socio_user.is_active = not socio_user.is_active
            socio_user.save()
            estado = "activo" if socio_user.is_active else "dado de baja"
            messages.success(request, f'Socio {socio_user.username} ahora está {estado}.')
            return redirect('admin_socios')

        # ALTA DE SOCIO (ADMIN) — Usuario y Contraseña = DNI
        elif accion == 'alta':
            dni = request.POST.get('dni', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            email = request.POST.get('email', '').strip()
            telefono = request.POST.get('telefono', '').strip()

            if Usuario.objects.filter(username=dni).exists():
                messages.error(request, f'Ya existe un socio con DNI {dni}.')
            else:
                nuevo_user = Usuario.objects.create_user(
                    username=dni,
                    email=email,
                    password=dni,
                    first_name=nombre,
                    last_name=apellido
                )
                nuevo_user.rol = 'socio'
                nuevo_user.is_active = True
                if hasattr(nuevo_user, 'dni'):
                    nuevo_user.dni = dni
                if hasattr(nuevo_user, 'telefono'):
                    nuevo_user.telefono = telefono
                nuevo_user.save()

                socio_kwargs = {'usuario': nuevo_user}
                if hasattr(Socio, 'dni'):
                    socio_kwargs['dni'] = dni
                if hasattr(Socio, 'telefono'):
                    socio_kwargs['telefono'] = telefono
                if hasattr(Socio, 'estado_cuenta'):
                    socio_kwargs['estado_cuenta'] = 'ROJO'
                
                Socio.objects.get_or_create(**socio_kwargs)

                messages.success(
                    request, 
                    f'Socio {nombre} {apellido} registrado con éxito. Acceso habilitado: Usuario: {dni} | Contraseña: {dni}'
                )
            return redirect('admin_socios')

    # 2. BÚSQUEDA Y FILTRADO
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

    # 3. ENRIQUECER DATOS (Estado real de cuota y baja automática a los 90 días)
    socios_lista = []
    for s in socios_qs:
        socio_obj = Socio.objects.filter(usuario=s).first()
        ultimo_vencimiento = None
        tiene_membresia_vigente = False

        if MembresiaSocio and socio_obj:
            ultima_memb = MembresiaSocio.objects.filter(socio=socio_obj).order_by('-fecha_fin').first()
            if ultima_memb:
                ultimo_vencimiento = ultima_memb.fecha_fin
                if ultima_memb.fecha_fin >= hoy and ultima_memb.activa:
                    tiene_membresia_vigente = True
                elif ultima_memb.fecha_fin < limite_3_meses and s.is_active:
                    # Baja automática si superó los 90 días vencido
                    s.is_active = False
                    s.save()
            else:
                if s.date_joined.date() < limite_3_meses and s.is_active:
                    s.is_active = False
                    s.save()

        es_verde = tiene_membresia_vigente or (
            socio_obj and getattr(socio_obj, 'estado_cuenta', '') == 'VERDE'
        )
        estado_cuota = 'VERDE' if es_verde else 'ROJO'

        # Solo guardar si el campo existe físicamente en el modelo Socio
        if socio_obj and 'estado_cuenta' in [f.name for f in socio_obj._meta.get_fields()]:
            if socio_obj.estado_cuenta != estado_cuota:
                socio_obj.estado_cuenta = estado_cuota
                socio_obj.save(update_fields=['estado_cuenta'])

        socios_lista.append({
            'usuario': s,
            'socio': socio_obj,
            'estado_cuota': estado_cuota,
            'ultimo_vencimiento': ultimo_vencimiento,
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
                messages.error(request, f'El DNI {dni} ya está registrado en el sistema.')
            else:
                nuevo_user = Usuario.objects.create_user(
                    username=dni,
                    email=email,
                    password='123',
                    first_name=nombre,
                    last_name=apellido
                )
                nuevo_user.rol = 'socio'
                nuevo_user.is_active = True
                if hasattr(nuevo_user, 'dni'):
                    nuevo_user.dni = dni
                if hasattr(nuevo_user, 'telefono'):
                    nuevo_user.telefono = telefono
                nuevo_user.save()

                socio_kwargs = {'usuario': nuevo_user}
                if hasattr(Socio, 'dni'):
                    socio_kwargs['dni'] = dni
                if hasattr(Socio, 'telefono'):
                    socio_kwargs['telefono'] = telefono
                if hasattr(Socio, 'estado_cuenta'):
                    socio_kwargs['estado_cuenta'] = 'ROJO'

                Socio.objects.get_or_create(**socio_kwargs)

                messages.success(
                    request, 
                    f'¡Socio {nombre} {apellido} registrado con éxito! Cuenta habilitada (Usuario: {dni} | Contraseña: 123).'
                )
            return redirect('padron_socios_empleado')

        # EDITAR SOCIO
        elif accion == 'editar':
            socio_id = request.POST.get('socio_id')
            socio_user = get_object_or_404(Usuario, id=socio_id, rol='socio')
            socio_user.first_name = request.POST.get('nombre', '').strip()
            socio_user.last_name = request.POST.get('apellido', '').strip()
            socio_user.email = request.POST.get('email', '').strip()
            
            telefono_in = request.POST.get('telefono', '').strip()
            if hasattr(socio_user, 'telefono'):
                socio_user.telefono = telefono_in
            socio_user.save()

            socio_profile = Socio.objects.filter(usuario=socio_user).first()
            if socio_profile and hasattr(socio_profile, 'telefono'):
                socio_profile.telefono = telefono_in
                socio_profile.save()

            messages.success(request, f'Datos de {socio_user.first_name} {socio_user.last_name} actualizados.')
            return redirect('padron_socios_empleado')

        # DAR DE BAJA / REACTIVAR
        elif accion == 'toggle_baja':
            socio_id = request.POST.get('socio_id')
            socio_user = get_object_or_404(Usuario, id=socio_id, rol='socio')
            socio_user.is_active = not socio_user.is_active
            socio_user.save()
            estado = "activo" if socio_user.is_active else "dado de baja"
            messages.success(request, f'El socio {socio_user.first_name} {socio_user.last_name} ahora está {estado}.')
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