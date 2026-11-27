from pathlib import Path
import os
import pymysql
pymysql.install_as_MySQLdb()
from django.db.backends.base.base import BaseDatabaseWrapper
BaseDatabaseWrapper.check_database_version_supported = lambda self: None
from django.db.backends.mysql.features import DatabaseFeatures
DatabaseFeatures.can_return_columns_from_insert = property(lambda self: False)
DatabaseFeatures.can_return_rows_from_bulk_insert = property(lambda self: False)


BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------------------------------
# CONFIGURACIÓN SECRETA: se lee del archivo .env (que NO se sube a GitHub; ver .env.example).
# Sin .env se usan los valores de desarrollo local de abajo.
def _cargar_env(ruta):
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding='utf-8').splitlines():
        linea = linea.strip()
        if linea and not linea.startswith('#') and '=' in linea:
            clave, valor = linea.split('=', 1)
            os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


_cargar_env(BASE_DIR / '.env')


def _env(clave, por_defecto=''):
    """Valor de la variable; si no está o quedó vacía en el .env, se usa el de por defecto."""
    return os.environ.get(clave) or por_defecto


SECRET_KEY = _env('DJANGO_SECRET_KEY', 'django-insecure-gymtrack-os-local-key-change-in-production')
DEBUG = _env('DJANGO_DEBUG', 'True').lower() in ('1', 'true', 'si', 'yes')
ALLOWED_HOSTS = [h.strip() for h in _env('DJANGO_ALLOWED_HOSTS').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = [f'https://{h}' for h in ALLOWED_HOSTS if h not in ('localhost', '127.0.0.1')]
if not DEBUG:
    # En el hosting el sitio va por HTTPS detrás de un proxy: así los links de los mails salen con https
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
# Apps nativas de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
# Apps del sistema GymTrack OS
    'usuarios',
    'socios',
    'membresias',
    'pagos',
    'actividades',
    'reservas',
    'rutinas',
    'asistencias',
    'novedades',
]

AUTH_USER_MODEL = 'usuarios.Usuario'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gymtrack.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'usuarios.context_processors.navegacion',
                'usuarios.context_processors.datos_gimnasio',
                'novedades.context_processors.novedades',
            ],
        },
    },
]

WSGI_APPLICATION = 'gymtrack.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': _env('DB_NAME', 'gymtrack'),
        'USER': _env('DB_USER', 'root'),
        'PASSWORD': _env('DB_PASSWORD', ''),
        'HOST': _env('DB_HOST', 'localhost'),
        'PORT': _env('DB_PORT', '3306'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static',]
# Carpeta donde 'python manage.py collectstatic' junta los estáticos para el hosting
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'inicio'

# --------------------------------------------------------------------------------------------------
# EMAIL (recuperar contraseña y Botón de Arrepentimiento)
# Con GYMTRACK_EMAIL y GYMTRACK_EMAIL_PASSWORD en el .env se manda por Gmail; sin ellos,
# los mails se imprimen en la terminal de runserver (sirve para probar sin cuenta).
EMAIL_HOST_USER = _env('GYMTRACK_EMAIL')
EMAIL_HOST_PASSWORD = _env('GYMTRACK_EMAIL_PASSWORD').replace(' ', '')
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = _env('GYMTRACK_EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(_env('GYMTRACK_EMAIL_PORT', '587'))
    EMAIL_USE_TLS = True
    EMAIL_TIMEOUT = 15
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = f"GymTrack <{EMAIL_HOST_USER or 'no-responder@gymtrack.local'}>"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# --------------------------------------------------------------------------------------------------
# DATOS LEGALES DEL GIMNASIO
# Se usan en los Términos y Condiciones, la Política de Privacidad y el Botón de Arrepentimiento.
# ⚠ SON DATOS DE EJEMPLO: reemplazarlos por los reales del gimnasio antes de publicar el sitio.
DATOS_GIMNASIO = {
    'nombre_fantasia': 'Bodynamic',
    'razon_social': 'Bodynamic S.R.L.',
    'cuit': '30-12345678-9',
    'domicilio': 'Av. San Martín 2975, Rosario, Santa Fe',
    'ciudad': 'Rosario, Santa Fe',
    'email': _env('GYMTRACK_EMAIL') or 'contacto@bodynamic.com.ar',
    'telefono': '+54 341 400-0000',
    'horario_atencion': 'Lunes a viernes de 7 a 22 hs y sábados de 9 a 13 hs',
    # N.º de inscripción de la base de datos en el Registro Nacional de Bases de Datos (AAIP)
    'registro_base_datos': 'En trámite',
    'terminos_actualizados': '26/11/2026',
    # Cuenta a la que transfieren los socios desde "Mis pagos"
    'transferencia_alias': 'BODYNAMIC.GYM.MP',
    'transferencia_cbu': '0000003100012345678901',
    'transferencia_titular': 'Bodynamic S.R.L.',
    'transferencia_banco': 'Mercado Pago',
}
