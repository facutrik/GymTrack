# usuarios/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone                   
from actividades.models import Actividad
from membresias.models import Plan
from usuarios.models import Usuario
from asistencias.models import Asistencia                

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
        
        context = {
            'total_socios': total_socios,
            'total_empleados': total_empleados,
            'total_actividades': total_actividades,
            'ingresos_mes': '0',
        }
        return render(request, 'admin/dashboard.html', context)
    
    # 2. Empleado / Recepción / Entrenador  👈 ACÁ AGREGAMOS LA CARGA DE ASISTENCIAS
    elif getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado'):
        hoy = timezone.localdate()
        asistencias_hoy = Asistencia.objects.filter(fecha_hora__date=hoy).count()
        ultimas_asistencias = Asistencia.objects.filter(
            fecha_hora__date=hoy
        ).select_related('socio__usuario').order_by('-fecha_hora')[:10]

        context = {
            'asistencias_hoy': asistencias_hoy,
            'ultimas_asistencias': ultimas_asistencias,
        }
        return render(request, 'empleado/dashboard.html', context)
    
    # 3. Socio (por defecto)
    else:
        actividades = Actividad.objects.all()
        return render(request, 'socio/dashboard.html', {'actividades': actividades})