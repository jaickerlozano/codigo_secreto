import os
import re
from pathlib import Path
from urllib.parse import urlparse

import environ
from corsheaders.defaults import default_headers
from django.core.exceptions import ImproperlyConfigured

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(BASE_DIR / '.env')

PRODUCTION_ENVIRONMENT = "production"
REQUIRED_PRODUCTION_SETTINGS = """
ENVIRONMENT SECRET_KEY DEBUG FRONTEND_ORIGIN API_HOSTNAME ALLOWED_HOSTS
CORS_ALLOWED_ORIGINS CSRF_TRUSTED_ORIGINS COOKIE_TOPOLOGY COOKIE_SITE_DOMAIN
TLS_TERMINATION NUM_PROXIES SECURE_HSTS_SECONDS DATABASE_URL LOG_LEVEL
EMAIL_HOST EMAIL_PORT EMAIL_HOST_USER EMAIL_HOST_PASSWORD DEFAULT_FROM_EMAIL
CLOUDINARY_CLOUD_NAME CLOUDINARY_API_KEY CLOUDINARY_API_SECRET CLOUDINARY_UPLOAD_PRESET
""".split()
PUBLIC_SUFFIXES = {
    "ac.uk", "app", "biz", "co.uk", "com", "dev", "edu", "gov", "io",
    "mil", "net", "org", "uk",
}
HOSTNAME_PATTERN = re.compile(
    r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}",
    re.IGNORECASE,
)


def validate_production_configuration(configuration):
    """Validate and normalize the only production topology this app supports."""
    errors = []
    values = {}
    for setting in REQUIRED_PRODUCTION_SETTINGS:
        raw_value = configuration.get(setting)
        values[setting] = "" if raw_value is None else str(raw_value).strip()
        if not values[setting]:
            errors.append(f"{setting} must be set for production.")

    def hostname(value, setting):
        value = value.lower()
        if not HOSTNAME_PATTERN.fullmatch(value) or value.endswith((".localhost", ".local")):
            errors.append(f"{setting} must be a non-local DNS hostname.")
            return None
        return value

    def positive_integer(setting):
        try:
            value = int(values[setting])
        except ValueError:
            errors.append(f"{setting} must be a positive integer.")
            return None
        if value < 1:
            errors.append(f"{setting} must be a positive integer.")
            return None
        return value

    def https_origin(value, setting):
        try:
            parsed = urlparse(value)
            port = parsed.port
        except ValueError:
            errors.append(f"{setting} must be a valid HTTPS origin.")
            return None, None
        if (
            parsed.scheme != "https"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
        ):
            errors.append(f"{setting} must be a valid HTTPS origin.")
            return None, None
        host = hostname(parsed.hostname or "", setting)
        return (f"https://{host}{f':{port}' if port else ''}", host) if host else (None, None)

    api_host = hostname(values["API_HOSTNAME"], "API_HOSTNAME")
    parent = hostname(values["COOKIE_SITE_DOMAIN"], "COOKIE_SITE_DOMAIN")
    frontend_origin, frontend_host = https_origin(values["FRONTEND_ORIGIN"], "FRONTEND_ORIGIN")
    lists = {
        setting: tuple(item.strip() for item in values[setting].split(","))
        for setting in ("ALLOWED_HOSTS", "CORS_ALLOWED_ORIGINS", "CSRF_TRUSTED_ORIGINS")
    }
    for setting, entries in lists.items():
        if not entries or any(not entry for entry in entries):
            errors.append(f"{setting} must be a non-empty list.")

    if values["ENVIRONMENT"] != PRODUCTION_ENVIRONMENT:
        errors.append("ENVIRONMENT must be production.")
    if values["DEBUG"].lower() not in {"false", "0", "no"}:
        errors.append("DEBUG must be False in production.")
    if len(values["SECRET_KEY"]) < 50 or values["SECRET_KEY"].startswith("django-insecure-"):
        errors.append("SECRET_KEY must be a non-default production secret.")
    if parent in PUBLIC_SUFFIXES:
        errors.append("COOKIE_SITE_DOMAIN must not be a public suffix.")
    if api_host and lists["ALLOWED_HOSTS"] != (api_host,):
        errors.append("ALLOWED_HOSTS must contain exactly API_HOSTNAME.")
    for setting in ("CORS_ALLOWED_ORIGINS", "CSRF_TRUSTED_ORIGINS"):
        if lists[setting] != (frontend_origin,):
            errors.append(f"{setting} must contain exactly FRONTEND_ORIGIN.")
    if values["COOKIE_TOPOLOGY"] != "shared-parent":
        errors.append("COOKIE_TOPOLOGY must be shared-parent.")
    for setting, host in (("API_HOSTNAME", api_host), ("FRONTEND_ORIGIN", frontend_host)):
        if host and parent and (host == parent or not host.endswith(f".{parent}")):
            errors.append(f"{setting} must be a descendant of COOKIE_SITE_DOMAIN.")
    if values["TLS_TERMINATION"] != "proxy":
        errors.append("TLS_TERMINATION must be proxy.")

    proxies = positive_integer("NUM_PROXIES")
    hsts_seconds = positive_integer("SECURE_HSTS_SECONDS")
    email_port = positive_integer("EMAIL_PORT")
    if email_port and email_port > 65535:
        errors.append("EMAIL_PORT must be a valid TCP port.")
    try:
        database = urlparse(values["DATABASE_URL"])
        database.port
    except ValueError:
        database = None
    if database is None or database.scheme not in {"postgres", "postgresql"} or not database.hostname or not database.path.strip("/") or not database.username or database.password is None:
        errors.append("DATABASE_URL must be a PostgreSQL URL with credentials.")
    elif not hostname(database.hostname, "DATABASE_URL"):
        pass
    if values["LOG_LEVEL"].upper() not in {"INFO", "WARNING", "ERROR", "CRITICAL"}:
        errors.append("LOG_LEVEL must be INFO, WARNING, ERROR, or CRITICAL.")
    hostname(values["EMAIL_HOST"], "EMAIL_HOST")
    if "@" not in values["DEFAULT_FROM_EMAIL"]:
        errors.append("DEFAULT_FROM_EMAIL must be a valid email address.")
    if errors:
        raise ImproperlyConfigured("Production configuration is invalid: " + " ".join(errors))

    values.update(lists)
    values.update({
        "DEBUG": False,
        "NUM_PROXIES": proxies,
        "SECURE_HSTS_SECONDS": hsts_seconds,
        "EMAIL_PORT": email_port,
        "LOG_LEVEL": values["LOG_LEVEL"].upper(),
        "csrf_cookie_domain": f".{parent}",
    })
    return values


ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").strip()
if ENVIRONMENT not in {"development", "test", PRODUCTION_ENVIRONMENT}:
    raise ImproperlyConfigured("ENVIRONMENT must be development, test, or production.")
PRODUCTION_CONFIGURATION = validate_production_configuration(
    {setting: os.environ.get(setting) for setting in REQUIRED_PRODUCTION_SETTINGS}
) if ENVIRONMENT == PRODUCTION_ENVIRONMENT else None

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')


def production_or_env(setting, default=None):
    return PRODUCTION_CONFIGURATION[setting] if PRODUCTION_CONFIGURATION else env(setting, default=default)


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = production_or_env("DEBUG", False)

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
EMAIL_HOST = production_or_env("EMAIL_HOST", "")
EMAIL_BACKEND = _resolve_email_backend(
    DEBUG, EMAIL_HOST, env("EMAIL_BACKEND", default=None)
)
EMAIL_PORT = production_or_env("EMAIL_PORT", 587)
EMAIL_USE_TLS = True if PRODUCTION_CONFIGURATION else env("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = production_or_env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = production_or_env("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = production_or_env("DEFAULT_FROM_EMAIL", "Código Secreto <no-reply@codigosecreto.cl>")
LOG_LEVEL = production_or_env("LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}

ALLOWED_HOSTS = list(PRODUCTION_CONFIGURATION["ALLOWED_HOSTS"]) if PRODUCTION_CONFIGURATION else ['localhost', '127.0.0.1']


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

def _resolve_database_config(database_url, *, production=False):
    if database_url:
        return environ.Env.db_url_config(database_url)
    if production:
        raise ImproperlyConfigured("DATABASE_URL must be set for production.")
    return {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }


DATABASE_URL = production_or_env("DATABASE_URL")
DATABASES = {'default': _resolve_database_config(DATABASE_URL, production=bool(PRODUCTION_CONFIGURATION))}


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
NUM_PROXIES = production_or_env("NUM_PROXIES")

SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https") if PRODUCTION_CONFIGURATION else None
)
USE_X_FORWARDED_HOST = False
SECURE_SSL_REDIRECT = bool(PRODUCTION_CONFIGURATION)
SECURE_HSTS_SECONDS = PRODUCTION_CONFIGURATION["SECURE_HSTS_SECONDS"] if PRODUCTION_CONFIGURATION else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = bool(PRODUCTION_CONFIGURATION)
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = bool(PRODUCTION_CONFIGURATION)
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Esto hace invisible el token para javascript
SIMPLE_JWT = {
    "JWT_AUTH_COOKIE": "access_token",  # Nombre de la cookie del token de acceso
    "JWT_AUTH_REFRESH_COOKIE": "refresh_token",
    "JWT_AUTH_HTTPONLY": True,
    "JWT_COOKIE_SECURE": bool(PRODUCTION_CONFIGURATION),
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

CORS_ALLOWED_ORIGINS = list(PRODUCTION_CONFIGURATION["CORS_ALLOWED_ORIGINS"]) if PRODUCTION_CONFIGURATION else [
    "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000",
    "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000",
]

CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
    "x-csrftoken",          # Requerido para CSRF cross-origin
    "content-type",
]

# Obligatorio para cookies cross-origin (diferentes puertos localhost)
CORS_ALLOW_CREDENTIALS = True

# CSRF Trusted Origins - OBLIGATORIO en Django 4+ para cross-origin
CSRF_TRUSTED_ORIGINS = list(PRODUCTION_CONFIGURATION["CSRF_TRUSTED_ORIGINS"]) if PRODUCTION_CONFIGURATION else CORS_ALLOWED_ORIGINS

# Cookie settings para cross-origin localhost (puerto 5173 -> 8000)
# "Lax" permite cookies en navegación cross-origin (top-level)
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = bool(PRODUCTION_CONFIGURATION)
CSRF_COOKIE_DOMAIN = PRODUCTION_CONFIGURATION["csrf_cookie_domain"] if PRODUCTION_CONFIGURATION else None
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = bool(PRODUCTION_CONFIGURATION)
SESSION_COOKIE_DOMAIN = None
GUEST_ORDER_ACCESS_COOKIE_SECURE = bool(PRODUCTION_CONFIGURATION)
GUEST_ORDER_ACCESS_COOKIE_SAMESITE = "Strict"

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
