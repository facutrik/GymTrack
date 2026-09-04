from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from actividades.models import Actividad
from membresias.models import Plan

def inicio_publico(request):
    # 1. Si ya inició sesión, no ve la portada; va directo a su panel
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # 2. Si NO inició sesión, ve la portada con la info pública del gimnasio
    actividades = Actividad.objects.all()
    planes = Plan.objects.all()
    
    context = {
        'actividades': actividades,
        'membresias': planes,
    }
    return render(request, 'publico/index.html', context)


@login_required
def dashboard(request):
    # Solo entran usuarios autenticados. Se evalúa el rol para renderizar el HTML correcto:
    user = request.user
    
    if user.is_superuser or getattr(user, 'es_admin', False):
        return render(request, 'admin/dashboard.html')
    elif getattr(user, 'es_empleado', False):
        return render(request, 'empleado/dashboard.html')
    
    return render(request, 'socio/dashboard.html')