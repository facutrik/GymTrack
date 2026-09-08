# usuarios/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from actividades.models import Actividad
from membresias.models import Plan

def inicio_publico(request):
    # Si ya inició sesión, no ve la landing; va directo a su panel
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Datos dinámicos para la landing pública
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
        return render(request, 'admin/dashboard.html')
    
    # 2. Empleado / Recepción / Entrenador
    elif getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado'):
        return render(request, 'empleado/dashboard.html')
    
    # 3. Socio (por defecto)
    else:
        return render(request, 'socio/dashboard.html')