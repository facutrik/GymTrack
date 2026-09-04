from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from usuarios import views

urlpatterns = [
    # Landing pública (Página principal para no logueados)
    path('', views.inicio_publico, name='inicio'),
    
    # Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='inicio'), name='logout'),
    
    # Panel privado del usuario
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Panel de administración de Django
    path('admin/', admin.site.urls),
]