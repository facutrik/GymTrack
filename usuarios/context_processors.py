"""
Datos que usa el nav de templates/base.html en todas las páginas internas.

El nav no tiene menú: a cada sección se entra desde las tarjetas del panel, y en el resto
de las páginas se muestra el botón "Volver al Panel".
"""

from django.conf import settings


def datos_gimnasio(request):
    """Datos legales del gimnasio (settings.DATOS_GIMNASIO) para el footer y las páginas legales."""
    return {'gimnasio': getattr(settings, 'DATOS_GIMNASIO', {})}


ETIQUETAS_ROL = {
    'admin': 'Administración',
    'recepcion': 'Recepción',
    'entrenador': 'Entrenador',
    'empleado': 'Personal',
    'socio': 'Socio',
}


def navegacion(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}

    rol = 'admin' if user.is_superuser else getattr(user, 'rol', 'socio')
    url_actual = getattr(getattr(request, 'resolver_match', None), 'url_name', None)
    return {
        'nav_rol': rol,
        'nav_rol_etiqueta': ETIQUETAS_ROL.get(rol, 'Socio'),
        'nav_en_panel': url_actual == 'dashboard',
    }
