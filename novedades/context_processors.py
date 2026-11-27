from novedades.models import LecturaNovedades, Novedad

ROLES_QUE_PUBLICAN = ('admin', 'recepcion', 'entrenador', 'empleado')


def puede_publicar(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'rol', None) in ROLES_QUE_PUBLICAN)


def novedades(request):
    """Novedades de la campana del nav (todas las páginas internas)."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    visibles = list(Novedad.objects.visibles().select_related('autor')[:15])
    lectura = LecturaNovedades.objects.filter(usuario=user).first()
    # Las que publicó uno mismo no cuentan como "sin leer"
    no_leidas = [n for n in visibles
                 if n.autor_id != user.id and (not lectura or n.publicada > lectura.vistas_hasta)]
    for n in visibles:
        n.nueva = n in no_leidas
    return {
        'novedades_campana': visibles,
        'novedades_no_leidas': len(no_leidas),
        'puede_publicar_novedades': puede_publicar(user),
    }
