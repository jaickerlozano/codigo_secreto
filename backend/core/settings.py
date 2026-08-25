from pathlib import Path
import environ
from corsheaders.defaults import default_headers

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# Payment provider; only "mock" is selectable, and only when DEBUG=True
PAYMENT_PROVIDER = env("PAYMENT_PROVIDER", default=None)

# Support WhatsApp line for special-delivery agreement guidance (E.164, no "+")
SUPPORT_WHATSAPP_PHONE = env("SUPPORT_WHATSAPP_PHONE", default="56953716242")


def _resolve_email_backend(debug, email_host, email_backend=None):
    """Deterministic backend precedence for development and production.

    DEBUG with a blank SMTP host forces the console backend; every other
    configuration uses env-driven TLS SMTP and never silently falls back to
    console in production.
    """
    if debug and not email_host:
        return "django.core.mail.backends.console.EmailBackend"
    if email_backend and "console" in email_backend:
        return "django.core.mail.backends.smtp.EmailBackend"
    return email_backend or "django.core.mail.backends.smtp.EmailBackend"


# Email for transactional notifications; env-driven, no secrets in the repo
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_BACKEND = _resolve_email_backend(
    DEBUG, EMAIL_HOST, env("EMAIL_BACKEND", default=None)
)
EMAIL_PORT = env("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Código Secreto <no-reply@codigosecreto.cl>")

ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage',

    'rest_framework',
    'drf_spectacular',
    'django_filters',
    'corsheaders',
    'cloudinary',

    'apps.products',
    'apps.authentication',
    'apps.shipping',
    'apps.carts',
    'apps.orders',
    'apps.payments',
    'apps.contact',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
    ],

    # Use page number pagination by default, with a page size of 10 items.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,

    # Use drf-spectacular's AutoSchema class by default for generating API schemas.
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    # Enable filtering by default using django-filter
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],

    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.authentication.authentication.CookieJWTAuthentication",
    ),

    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "login": env("THROTTLE_LOGIN", default="5/min"),
        "register": env("THROTTLE_REGISTER", default="3/hour"),
        "order_create": env("THROTTLE_ORDER_CREATE", default="10/hour"),
        "order_lookup": env("THROTTLE_ORDER_LOOKUP", default="30/min"),
        "order_quote": env("THROTTLE_ORDER_QUOTE", default="30/min"),
        "payment_initiate": env("THROTTLE_PAYMENT_INITIATE", default="10/min"),
        "payment_approve": env("THROTTLE_PAYMENT_APPROVE", default="10/min"),
        "contact_message": env("THROTTLE_CONTACT_MESSAGE", default="5/hour"),
    },
}

# Number of proxy hops the deployment uses. Keep None/0 to avoid trusting
# arbitrary X-Forwarded-For headers; set to the actual proxy count only.
NUM_PROXIES = env("NUM_PROXIES", default=None)

# Esto hace invisible el token para javascript
SIMPLE_JWT = {
    "JWT_AUTH_COOKIE": "access_token",  # Nombre de la cookie del token de acceso
    "JWT_AUTH_REFRESH_COOKIE": "refresh_token",
    "JWT_AUTH_HTTPONLY": True,
    "JWT_COOKIE_SECURE": False,  # Dev: True en producción con HTTPS
    "JWT_COOKIE_SAMESITE": "Lax",
    "JWT_COOKIE_PATH": "/",
}

# Settings for drf-spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'Código Secreto Management API',
    'DESCRIPTION': 'API for managing products, suppliers, and categories in the Código Secreto inventory system.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # OTHER SETTINGS
}

AUTH_USER_MODEL = 'authentication.User'

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",          # Vite default
    "http://127.0.0.1:5173",
    "http://localhost:3000",          # Create React App / Next.js default
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
    "x-csrftoken",          # Requerido para CSRF cross-origin
    "content-type",
]

# Obligatorio para cookies cross-origin (diferentes puertos localhost)
CORS_ALLOW_CREDENTIALS = True

# CSRF Trusted Origins - OBLIGATORIO en Django 4+ para cross-origin
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Cookie settings para cross-origin localhost (puerto 5173 -> 8000)
# "Lax" permite cookies en navegación cross-origin (top-level)
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = False          # True solo en producción con HTTPS
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False       # True solo en producción con HTTPS

# Configura el almacenamiento de archivos multimedia para que apunte a Cloudinary
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Credenciales de Cloudinary
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': env('CLOUDINARY_CLOUD_NAME'), 
    'API_KEY': env('CLOUDINARY_API_KEY'),
    'API_SECRET': env('CLOUDINARY_API_SECRET'),
    'UPLOAD_PRESET': env('CLOUDINARY_UPLOAD_PRESET'), 
}
