import logging
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from novedades.context_processors import puede_publicar
from novedades.models import LecturaNovedades, Novedad

logger = logging.getLogger(__name__)


@login_required
@require_POST
def marcar_leidas(request):
    """La campana llama a esto al abrirse: el número de "no leídas" vuelve a cero."""
    LecturaNovedades.objects.update_or_create(usuario=request.user, defaults={'vistas_hasta': timezone.now()})
    return JsonResponse({'ok': True})


def _avisar_por_mail(novedad):
    """Un solo mail con todos los socios activos en copia oculta. Devuelve cuántos lo recibieron."""
    destinatarios = list(
        get_user_model().objects.filter(rol='socio', is_active=True).exclude(email='')
        .values_list('email', flat=True).distinct()
    )
    if not destinatarios:
        return 0
    gimnasio = getattr(settings, 'DATOS_GIMNASIO', {})
    cuerpo = (
        f'{novedad.mensaje}\n\n'
        f'Podés ver todas las novedades en la campana de tu portal de socio.\n\n'
        f'{gimnasio.get("nombre_fantasia", "GymTrack")} · {gimnasio.get("domicilio", "")}'
    )
    try:
        EmailMessage(f'[{gimnasio.get("nombre_fantasia", "GymTrack")}] {novedad.titulo}', cuerpo,
                     settings.DEFAULT_FROM_EMAIL, to=[settings.EMAIL_HOST_USER or settings.DEFAULT_FROM_EMAIL],
                     bcc=destinatarios).send()
        return len(destinatarios)
    except Exception:
        logger.exception('No se pudo mandar la novedad "%s" por mail', novedad.titulo)
        return None


def _datos_del_formulario(request):
    hasta = request.POST.get('visible_hasta', '').strip()
    try:
        visible_hasta = datetime.strptime(hasta, '%Y-%m-%d').date() if hasta else None
    except ValueError:
        visible_hasta = None
    categoria = request.POST.get('categoria', 'general')
    return {
        'titulo': request.POST.get('titulo', '').strip()[:120],
        'mensaje': request.POST.get('mensaje', '').strip(),
        'categoria': categoria if categoria in dict(Novedad.CATEGORIAS) else 'general',
        'visible_hasta': visible_hasta,
    }


@login_required
def gestionar_novedades(request):
    if not puede_publicar(request.user):
        return redirect('dashboard')

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion in ('crear', 'editar'):
            datos = _datos_del_formulario(request)
            if not datos['titulo'] or not datos['mensaje']:
                messages.error(request, 'La novedad necesita un título y un mensaje.')
                return redirect('novedades')
            if accion == 'crear':
                novedad = Novedad.objects.create(autor=request.user, **datos)
                texto = f'Publicaste "{novedad.titulo}". Ya la ven todos en la campana.'
            else:
                novedad = get_object_or_404(Novedad, id=request.POST.get('novedad_id'))
                for campo, valor in datos.items():
                    setattr(novedad, campo, valor)
                novedad.save()
                texto = f'Guardaste los cambios de "{novedad.titulo}".'
            if request.POST.get('avisar_mail') == '1':
                enviados = _avisar_por_mail(novedad)
                if enviados:
                    novedad.avisada_por_mail = True
                    novedad.save(update_fields=['avisada_por_mail'])
                    texto += f' También se la mandamos por mail a {enviados} socio{"s" if enviados != 1 else ""}.'
                elif enviados == 0:
                    texto += ' No hay socios activos con email para avisarles.'
                else:
                    messages.warning(request, 'La novedad se publicó, pero no se pudo mandar el mail a los socios.')
            messages.success(request, texto)
        elif accion == 'archivar':
            novedad = get_object_or_404(Novedad, id=request.POST.get('novedad_id'))
            novedad.activa = not novedad.activa
            novedad.save(update_fields=['activa'])
            messages.success(request, f'"{novedad.titulo}" {"vuelve a mostrarse" if novedad.activa else "se archivó y ya no se muestra"}.')
        elif accion == 'eliminar':
            novedad = get_object_or_404(Novedad, id=request.POST.get('novedad_id'))
            novedad.delete()
            messages.success(request, f'Eliminaste "{novedad.titulo}".')
        return redirect('novedades')

    return render(request, 'novedades/gestionar.html', {
        'novedades': Novedad.objects.select_related('autor').all(),
        'categorias': Novedad.CATEGORIAS,
        'hoy': timezone.localdate(),
    })
