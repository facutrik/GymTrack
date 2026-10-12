from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from usuarios import views as usuarios_views
from socios import views as socios_views
from pagos import views as pagos_views

urlpatterns = [
    # Portada pública (Landing)
    path('', usuarios_views.inicio_publico, name='inicio'),

    # Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='inicio'), name='logout'),

    # Dashboard principal por roles
    path('dashboard/', usuarios_views.dashboard, name='dashboard'),

    # Módulos Administrador
    path('admin-panel/socios/', socios_views.admin_socios, name='admin_socios'),
    path('admin-panel/empleados/', usuarios_views.admin_empleados, name='admin_empleados'),
    path('admin-panel/pagos/', pagos_views.admin_pagos, name='admin_pagos'),

    # Django Admin nativo
    path('admin/', admin.site.urls),
]