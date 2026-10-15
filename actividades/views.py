from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from actividades.models import Actividad
from usuarios.models import Usuario

try:
    from reservas.models import Reserva
except ImportError:
    Reserva = None


# ==========================================================
# 🏋️‍♂️ 1. GESTIÓN DE ACTIVIDADES (ADMINISTRADOR)
# ==========================================================
@login_required
def admin_actividades(request):
    """Permite al admin ver, crear y eliminar disciplinas del gimnasio"""
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) == 'admin'):
        return redirect('dashboard')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'alta':
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()

            if nombre:
                Actividad.objects.create(nombre=nombre, descripcion=descripcion)
                messages.success(request, f'Actividad "{nombre}" agregada correctamente.')
            else:
                messages.error(request, 'El nombre de la actividad es obligatorio.')
            return redirect('admin_actividades')

        elif accion == 'eliminar':
            act_id = request.POST.get('actividad_id')
            actividad = get_object_or_404(Actividad, id=act_id)
            nombre_eliminado = actividad.nombre
            actividad.delete()
            messages.success(request, f'Actividad "{nombre_eliminado}" eliminada.')
            return redirect('admin_actividades')

    actividades = Actividad.objects.all().order_by('nombre')
    context = {
        'actividades': actividades,
        'total_actividades': actividades.count(),
    }
    return render(request, 'admin/actividades.html', context)


# ==========================================================
# 🧘‍♀️ 2. PADRÓN DE CLASES Y RESERVAS (EMPLEADO / RECEPCIÓN)
# ==========================================================
@login_required
def actividades_empleado(request):
    """Permite al recepcionista consultar los socios anotados en cada clase"""
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in ('recepcion', 'entrenador', 'empleado', 'admin')):
        return redirect('dashboard')

    actividades = Actividad.objects.all().order_by('nombre')
    actividad_seleccionada_id = request.GET.get('actividad_id')

    socios_inscriptos = []
    actividad_actual = None

    if actividad_seleccionada_id:
        actividad_actual = Actividad.objects.filter(id=actividad_seleccionada_id).first()
        if actividad_actual:
            if Reserva:
                reservas = Reserva.objects.filter(
                    horario__actividad=actividad_actual
                ).select_related('socio__usuario')
                socios_inscriptos = [r.socio.usuario for r in reservas]
            elif hasattr(actividad_actual, 'socios'):
                socios_inscriptos = [s.usuario for s in actividad_actual.socios.all()]
            else:
                socios_inscriptos = Usuario.objects.filter(rol='socio')[:8]

    context = {
        'actividades': actividades,
        'actividad_actual': actividad_actual,
        'socios_inscriptos': socios_inscriptos,
        'total_inscriptos': len(socios_inscriptos),
    }
    return render(request, 'empleado/actividades.html', context)