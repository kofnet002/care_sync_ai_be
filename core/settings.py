"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 5.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
from datetime import timedelta
import environ
import os
from celery.schedules import crontab

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.environ.get("DEBUG", default=0))

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS').split(',')
CORS_ORIGIN_WHITELIST = os.getenv('CORS_ORIGIN_WHITELIST', '').split(',')
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'django_filters',
    'google.generativeai',
    'django_celery_beat',
    'django_celery_results',
    
    # Local apps
    'apps.doctor',
    'apps.patient',
    'apps.user',
]

MIDDLEWARE = [
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

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

if os.getenv('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME':     os.getenv('DB_NAME'),
            'USER':     os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASS'),
            'HOST':     os.getenv('DB_HOST'),
            'PORT':     os.getenv('DB_PORT'),
            # 'OPTIONS': {
            #     'sslmode': 'require',  # Use 'require' for SSL encryption if needed
            # },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/


DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_ROOT = BASE_DIR / 'static/images/'
MEDIA_URL = '/images/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': ('api.utils.renderers.CustomResponseRenderer',),
    'EXCEPTION_HANDLER': 'api.utils.validation.custom_exception_handler',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
      'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.JSONParser',
     ],
     'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
     ],
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.BasicPagination',

    # Test
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',

    'TEST_REQUEST_RENDERER_CLASSES': [
        'rest_framework.renderers.MultiPartRenderer',
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.TemplateHTMLRenderer'
    ]
}

# Spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'CareSyncAI API',
    'DESCRIPTION': 'CareSyncAI Hospital Management System API based on the OpenAPI 3.0 specification.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVE_PUBLIC': False,
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
        # Disable warning logs
    'DISABLE_ERRORS_AND_WARNINGS': True,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    
    'SCHEMA_PATH_PREFIX': '/api/',
    'SWAGGER_UI_SETTINGS': {
        'tagsSorter': 'alpha',
        'operationsSorter': 'alpha',
    },
    'TAG_PLUGINS': [
        'drf_spectacular.contrib.django_filters.DjangoFilterPlugin',
    ],
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    'EXTERNAL_DOCS': {
        'description': 'Find out more about Swagger',
        'url': 'http://swagger.io',
    },
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'ISSUER': None,'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    # Disable warning logs
    'DISABLE_ERRORS_AND_WARNINGS': True,
    'SERVE_PUBLIC': False,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],  # Permissions for schema view
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {'type': 'apiKey', 'name': 'Authorization', 'in': 'header'},
        'Basic': {'type': 'basic'},
    }
}


AUTH_USER_MODEL = 'user.User'

GEMINI_API_KEY = env('GEMINI_API_KEY')

# REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_HOST = os.getenv('REDIS_HOST', 'caresyncai_redis')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_SSL  =  bool(int(os.getenv('REDIS_SSL', 0)))
REDIS_PASS = os.getenv('REDIS_PRIMARY_PASS', '')
REDIS_USER = os.getenv('REDIS_USER', 'default')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}',
    }
}

# Channel layer configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

# Celery Configuration
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:6379/0'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_RESULT_PERSISTENT = True
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = 'django_celery_beat.schedulers:DatabaseScheduler'

# CELERY BEAT SETTINGS
# CELERY_BEAT_SCHEDULE = {
#     "Send Reminder Emails": {
#         "task": "users.tasks.check_and_send_due_reminders",
#         "schedule": crontab(minute="*/5"),  # Run every 5 minutes
#     }
# }

# For celery
if REDIS_SSL:
    BROKER_URL = f'redis://{REDIS_USER}:{REDIS_PASS}@{REDIS_HOST}:{REDIS_PORT}/0?ssl_cert_reqs=required'
else:    
    # BROKER_URL = 'redis://127.0.0.1:6379/0'
    BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'

# Email settings (configure your email backend)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'noeljoel61@gmail.com'
EMAIL_HOST_PASSWORD = 'lizgbannzucyhqvk'

EMAIL_TOKEN_EXPIRATION_MINUTES = int(os.getenv("EMAIL_TOKEN_EXPIRATION_MINUTES", 30))
PASSWORD_TOKEN_EXPIRATION_MINUTES  = int(os.getenv("PASSWORD_TOKEN_EXPIRATION_MINUTES", 15))

UI_DOMAIN = os.getenv("UI_DOMAIN", "http://localhost:3000")

ADMIN_SITE_HEADER = 'CareSyncAI Admin'
ADMIN_SITE_TITLE = 'CareSyncAI Admin'
ADMIN_SITE_INDEX_TITLE = 'CareSyncAI Admin'