from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    if request.user.is_superuser:
        return render(request, 'admin/dashboard.html')
    elif request.user.rol in ('recepcion', 'entrenador', 'admin'):
        return render(request, 'empleado/dashboard.html')
    else:
        return render(request, 'socio/dashboard.html')