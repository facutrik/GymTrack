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

# Recuperación de contra (Login)
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

# Cambio de contra (Usuario logueado)
    path('cambiar-password/', auth_views.PasswordChangeView.as_view(
        template_name='recuperar_password.html',
        success_url='/dashboard/'
    ), name='cambiar_password'),

# Selector central de dashboard
    path('dashboard/', usuarios_views.dashboard, name='dashboard'),

# Modulo Admin
    path('admin-panel/socios/', socios_views.admin_socios, name='admin_socios'),
    path('admin-panel/empleados/', usuarios_views.admin_empleados, name='admin_empleados'),
    path('admin-panel/actividades/', usuarios_views.admin_actividades, name='admin_actividades'),
    path('admin-panel/membresias/', usuarios_views.admin_membresias, name='admin_membresias'),
    path('admin-panel/pagos/', pagos_views.admin_pagos, name='admin_pagos'),

# Modulo Recepcion
    path('empleado/asistencia/', asistencias_views.registrar_asistencia, name='registrar_asistencia'),
    path('empleado/socios/', socios_views.padron_socios_empleado, name='padron_socios_empleado'),
    path('empleado/pagos/', pagos_views.pagos_empleado, name='pagos_empleado'),       
    path('empleado/reservas/', actividades_views.reservas_empleado, name='reservas_empleado'),

# Modulo Socio
path('socio/mi-rutina/', usuarios_views.mi_rutina_socio, name='mi_rutina'),
path('socio/mis-reservas/', usuarios_views.mis_reservas_socio, name='mis_reservas'),
path('socio/mis-pagos/', usuarios_views.mis_pagos_socio, name='mis_pagos'),
path('socio/mi-perfil/', usuarios_views.mi_perfil_socio, name='mi_perfil'),

# Django Admin nativo
    path('admin/', admin.site.urls),
]