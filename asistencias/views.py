# asistencias/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from usuarios.models import Usuario
from socios.models import Socio
from asistencias.models import Asistencia

@login_required
def registrar_asistencia(request):
    user = request.user
    if not (user.is_superuser or getattr(user, 'rol', None) in ('recepcion', 'empleado', 'admin')):
        return redirect('dashboard')

    socio_encontrado = None
    estado_acceso = None

    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()
        
        try:
            # Buscamos por username (donde se guarda el DNI)
            usuario_socio = Usuario.objects.get(username=dni, rol='socio')
            
            # Obtenemos el socio por perfil_socio o Socio.objects
            if hasattr(usuario_socio, 'perfil_socio'):
                socio = usuario_socio.perfil_socio
            else:
                socio = Socio.objects.get(usuario=usuario_socio)
                
            socio_encontrado = socio

            # Validamos el estado de cuenta
            if getattr(socio, 'estado_cuenta', 'VERDE').upper() == 'VERDE':
                # Guardamos la asistencia en la base de datos
                Asistencia.objects.create(
                    socio=socio,
                    fecha_hora=timezone.now()
                )
                estado_acceso = 'verde'
            else:
                estado_acceso = 'rojo'

        except (Usuario.DoesNotExist, Socio.DoesNotExist):
            estado_acceso = 'no_encontrado'

    # Consultamos las asistencias reales de hoy
    hoy = timezone.localdate()
    asistencias_hoy_count = Asistencia.objects.filter(fecha_hora__date=hoy).count()
    ultimas_asistencias = Asistencia.objects.filter(
        fecha_hora__date=hoy
    ).select_related('socio__usuario').order_by('-fecha_hora')[:10]

    context = {
        'socio': socio_encontrado,
        'estado_acceso': estado_acceso,
        'asistencias_hoy': asistencias_hoy_count,
        'ultimas_asistencias': ultimas_asistencias,
    }
    return render(request, 'empleado/dashboard.html', context)