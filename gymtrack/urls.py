from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from usuarios import views as usuarios_views
from socios import views as socios_views
from pagos import views as pagos_views
from actividades import views as actividades_views
from asistencias import views as asistencias_views

urlpatterns = [
# Portada pública y autenticación
    path('', usuarios_views.inicio_publico, name='inicio'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='inicio'), name='logout'),

# Recuperación de contraseña (Login)
    path('recuperar-password/', auth_views.PasswordResetView.as_view(
        template_name='recuperar_password.html',
        email_template_name='recuperar_password_email.html',
        success_url='/recuperar-password/enviado/'
    ), name='recuperar_password'),
    path('recuperar-password/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='recuperar_password_enviado.html'
    ), name='password_reset_done'),
    path('recuperar-password/confirmar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='recuperar_password_confirmar.html',
        success_url='/recuperar-password/completado/'
    ), name='password_reset_confirm'),
    path('recuperar-password/completado/', auth_views.PasswordResetCompleteView.as_view(
        template_name='recuperar_password_completado.html'
    ), name='password_reset_complete'),

# Cambio de contraseña (Usuario logueado)
    path('cambiar-password/', auth_views.PasswordChangeView.as_view(
        template_name='recuperar_password.html',
        success_url='/dashboard/'
    ), name='cambiar_password'),

# Selector central de dashboard
    path('dashboard/', usuarios_views.dashboard, name='dashboard'),

# Panel Administrador
    path('admin-panel/socios/', socios_views.admin_socios, name='admin_socios'),
    path('admin-panel/empleados/', usuarios_views.admin_empleados, name='admin_empleados'),
    path('admin-panel/actividades/', usuarios_views.admin_actividades, name='admin_actividades'),
    path('admin-panel/membresias/', usuarios_views.admin_membresias, name='admin_membresias'),
    path('admin-panel/pagos/', pagos_views.admin_pagos, name='admin_pagos'),

# Módulo Empleado / Recepción
    path('empleado/asistencia/', asistencias_views.registrar_asistencia, name='registrar_asistencia'),
    path('empleado/socios/', socios_views.padron_socios_empleado, name='padron_socios_empleado'),
    path('empleado/actividades/', actividades_views.actividades_empleado, name='actividades_empleado'),
    path('empleado/perfil/', usuarios_views.mi_perfil_empleado, name='mi_perfil_empleado'),

# Django Admin nativo
    path('admin/', admin.site.urls),
]