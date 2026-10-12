# usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone

from actividades.models import Actividad
from membresias.models import Plan
from usuarios.models import Usuario
from pagos.models import Pago


def inicio_publico(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    actividades = Actividad.objects.all()
    planes = Plan.objects.all()
    
    context = {
        'actividades': actividades,
        'membresias': planes,
    }
    return render(request, 'publico/index.html', context)


@login_required
def dashboard(request):
    user = request.user
    
    # 1. Administrador (Superusuario o rol admin)
    if user.is_superuser or getattr(user, 'rol', None) == 'admin':
        total_socios = Usuario.objects.filter(rol='socio').count()
        total_empleados = Usuario.objects.filter(rol__in=['recepcion', 'entrenador', 'empleado']).count()
        total_actividades = Actividad.objects.count()
        
        # Ingresos del mes corriente
        hoy = timezone.localdate()
        total_mes = Pago.objects.filter(
            fecha_pago__year=hoy.year,
            fecha_pago__month=hoy.month
        ).aggregate(total=Sum('monto'))['total'] or 0

        context = {
            'total_socios': total_socios,
            'total_empleados': total_empleados,
            'total_actividades': total_actividades,
            'ingresos_mes': f"{total_mes:,.0f}".replace(',', '.'),
        }
        return render(request, 'admin/dashboard.html', context)
    
    # 2. Empleado / Recepción / Entrenador
    elif getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado'):
        return render(request, 'empleado/dashboard.html')
    
    # 3. Socio
    else:
        actividades = Actividad.objects.all()
        return render(request, 'socio/dashboard.html', {'actividades': actividades})


@login_required
def admin_empleados(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # Acción: Dar de baja o reactivar
        if accion == 'toggle_baja':
            emp_id = request.POST.get('empleado_id')
            empleado = get_object_or_404(Usuario, id=emp_id)
            if empleado == user:
                messages.error(request, 'No podés dar de baja tu propio usuario administrador.')
            else:
                empleado.is_active = not empleado.is_active
                empleado.save()
                estado = "activo" if empleado.is_active else "dado de baja"
                messages.success(request, f'El usuario {empleado.username} ahora está {estado}.')
            return redirect('admin_empleados')

        # Acción: Alta de empleado
        elif accion == 'alta':
            username = request.POST.get('username', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            email = request.POST.get('email', '').strip()
            rol = request.POST.get('rol', 'recepcion').strip()
            password = request.POST.get('password', '').strip() or '123'

            if Usuario.objects.filter(username=username).exists():
                messages.error(request, f'El nombre de usuario o DNI {username} ya está en uso.')
            else:
                nuevo_emp = Usuario.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=nombre,
                    last_name=apellido
                )
                nuevo_emp.rol = rol
                nuevo_emp.is_staff = True
                nuevo_emp.save()
                messages.success(request, f'Empleado {nombre} {apellido} ({rol.capitalize()}) creado con éxito.')
                return redirect('admin_empleados')

    query = request.GET.get('q', '').strip()
    filtro_rol = request.GET.get('rol', 'todos')

    empleados = Usuario.objects.filter(rol__in=['recepcion', 'entrenador', 'admin', 'empleado']).order_by('-date_joined')

    if query:
        empleados = empleados.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    if filtro_rol != 'todos':
        empleados = empleados.filter(rol=filtro_rol)

    context = {
        'empleados': empleados,
        'query': query,
        'filtro_rol': filtro_rol,
        'total_empleados': empleados.count(),
    }
    return render(request, 'admin/empleados.html', context)