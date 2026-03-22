"""
CONFIGURACIÓN DEL PROYECTO — Sistema de Farmacia Grupo 6
=========================================================
Misma estructura que el proyecto de referencia api_tienda:
  - python-decouple para leer variables de entorno (.env)
  - dj-database-url para parsear DATABASE_URL
  - DRF con TokenAuthentication
  - CORS habilitado
"""

from pathlib import Path
import dj_database_url
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

def _parse_debug(value):
    """
    CAMBIO: hacemos el parseo de DEBUG más tolerante (por ejemplo, DEBUG=release → False).
    python-decouple interpreta bool usando valores tipo true/false/1/0.
    En este proyecto a veces se usa DEBUG=release, que debe mapear a False.
    """
    if isinstance(value, bool):
        return value
    v = str(value).strip().lower()
    if v in {'1', 'true', 't', 'yes', 'y', 'on', 'debug'}:
        return True
    if v in {'0', 'false', 'f', 'no', 'n', 'off', 'release', 'prod', 'production'}:
        return False
    raise ValueError(f"Invalid truth value: {value}")

# ─────────────────────────────────────────────
# SEGURIDAD
# ─────────────────────────────────────────────
SECRET_KEY    = config('SECRET_KEY')
DEBUG         = config('DEBUG', default=False, cast=_parse_debug)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())

# ─────────────────────────────────────────────
# APLICACIONES INSTALADAS
# ─────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # ─ Librerías de terceros ─
    'rest_framework',            # Django REST Framework
    'rest_framework.authtoken',  # Autenticación por token
    'corsheaders',               # Permite peticiones desde otros dominios

    # ─ Nuestra app ─
    'farmacia',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # CorsMiddleware DEBE ir ANTES de CommonMiddleware
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ─────────────────────────────────────────────
# BASE DE DATOS — PostgreSQL en Supabase
# ─────────────────────────────────────────────
# dj_database_url.config() lee DATABASE_URL del .env y la convierte
# al formato que Django entiende (ENGINE, NAME, USER, PASSWORD, HOST, PORT).
# conn_max_age=600 mantiene conexiones abiertas 10 minutos (mejor rendimiento)
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
    )
}

# ─────────────────────────────────────────────
# DJANGO REST FRAMEWORK (DRF)
# ─────────────────────────────────────────────
REST_FRAMEWORK = {
    # TokenAuthentication: el cliente envía el token en el header:
    #   Authorization: Token abc123def456...
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],

    # CAMBIO: exige autenticacion para cualquier request (GET/POST/PUT/PATCH/DELETE)
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Paginación automática
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
}

# ─────────────────────────────────────────────
# CORS — Cross-Origin Resource Sharing
# ─────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173,http://localhost:3000',
    cast=Csv()
)

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE     = 'America/Bogota'
USE_I18N      = True
USE_TZ        = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
