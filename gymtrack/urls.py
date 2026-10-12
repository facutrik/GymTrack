# gymtrack/urls.py
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from asistencias import views as asistencias_views
from usuarios import views

urlpatterns = [
    # 1. Landing pública (raíz)
    path('', views.inicio_publico, name='inicio'),
    
    # 2. Login y Logout
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='inicio'), name='logout'),
    
    # 3. Dashboard (redirige según rol)
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # 4. Panel nativo de Django
    path('admin/', admin.site.urls),

    # 5. Panel Empleado / Recepción: Control de Ingresos por DNI
    path('empleado/asistencia/', asistencias_views.registrar_asistencia, name='registrar_asistencia'),
]   