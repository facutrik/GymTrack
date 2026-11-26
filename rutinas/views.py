import json
from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import RegistroUltimaSerie

PESO_MAXIMO = Decimal('9999.99')
REPS_MAXIMAS = 10000


def obtener_recordatorios(usuario):
    """Último peso y repeticiones de cada serie del usuario, como JSON para el template."""
    return json.dumps({
        r.clave_serie: {
            'kg': float(r.peso_kg) if r.peso_kg is not None else '',
            'reps': r.repeticiones if r.repeticiones is not None else '',
        }
        for r in RegistroUltimaSerie.objects.filter(usuario=usuario)
    })


def _leer_peso(valor):
    try:
        peso = Decimal(str(valor).strip().replace(',', '.'))
    except InvalidOperation:
        return None
    return peso if peso.is_finite() and 0 <= peso <= PESO_MAXIMO else None


def _leer_reps(valor):
    try:
        reps = int(float(str(valor).strip()))
    except (ValueError, OverflowError):
        return None
    return reps if 0 <= reps <= REPS_MAXIMAS else None


@login_required
@require_POST
def guardar_ultima_sesion(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    series = payload.get('series') if isinstance(payload, dict) else None
    if not isinstance(series, list):
        return JsonResponse({'ok': False, 'error': 'Formato de series inválido'}, status=400)

    largo_clave = RegistroUltimaSerie._meta.get_field('clave_serie').max_length
    guardadas = 0
    for item in series:
        if not isinstance(item, dict):
            continue
        clave = str(item.get('clave_serie') or '').strip()
        if not clave or len(clave) > largo_clave:
            continue

        # Sobrescribe siempre el último registro de esta serie para este usuario
        RegistroUltimaSerie.objects.update_or_create(
            usuario=request.user,
            clave_serie=clave,
            defaults={
                'peso_kg': _leer_peso(item.get('kg')),
                'repeticiones': _leer_reps(item.get('reps')),
            },
        )
        guardadas += 1

    return JsonResponse({'ok': True, 'guardadas': guardadas})
