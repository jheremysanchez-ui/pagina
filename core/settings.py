from pathlib import Path
import os
import environ
from datetime import timedelta
from corsheaders.defaults import default_headers

env = environ.Env()
environ.Env.read_env()

ENVIRONMENT = env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', defaul=False)

DOMAIN = os.environ.get('DOMAIN')

ALLOWED_HOSTS = [
    'www.fullpcstore.com',
    'fullpcstore.com',
    ]

#RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
#if RENDER_EXTERNAL_HOSTNAME:
 #   ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

PROJECT_APP = [
    'apps.user',
    'apps.user_profile',
]

ECOMMERCE_APP = [
    'apps.category',
    'apps.product',
    'apps.cart', 
    'apps.shipping', 
    'apps.orders', 
    'apps.payment', 
    'apps.coupons', 
    'apps.wishlist',
    'apps.reviews',   
]

THIRD_PARTY_APP = [
    'corsheaders',
    'rest_framework',
    'djoser',
    'social_django',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'ckeditor',
    'ckeditor_uploader',
]

INSTALLED_APPS = DJANGO_APPS + PROJECT_APP + ECOMMERCE_APP + THIRD_PARTY_APP

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'autoParagraph': False
    }
}

CKEDITOR_UPLOAD_PATH = "/media/"

MIDDLEWARE = [
    #'csp.middleware.CSPMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
        'DIRS': [os.path.join(BASE_DIR, 'build')],
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

DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres:///pagina"),
}

DATABASES["default"]["ATOMIC_REQUESTS"] = True

CORS_ALLOWED_ORIGINS  = [
    'http://127.0.0.1:8000',
    'http://127.0.0.1:3000',
    'https://fullpcstore.com',
    'https://www.fullpcstore.com',
]

CORS_ALLOW_HEADERS = list(default_headers) + [
    'authorization',
    'content-type',
]


CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://127.0.0.1:3000',
    'https://fullpcstore.com',
    'https://www.fullpcstore.com',
]

# En producción, acctivar estas opciones de seguridad

SESSION_COOKIE_SECURE = True

SECURE_SSL_REDIRECT = True

CSRF_COOKIE_SECURE = True


SECURE_HSTS_SECONDS = 31536000

SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_HSTS_PRELOAD = True


SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_BROWSER_XSS_FILTER = True


X_FRAME_OPTIONS = 'DENY'


# si usas Nginx como proxy:
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

#SESSION_COOKIE_HTTPONLY = False




PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# Password validation
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
LANGUAGE_CODE = 'es-ec'

TIME_ZONE = 'America/Guayaquil'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'build/static')
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 12
}

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('JWT', ),
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_TOKEN_CLASSES': (
        'rest_framework_simplejwt.tokens.AccessToken',
    )
}

DJOSER = {
    'LOGIN_FIELD': 'email',
    'USER_CREATE_PASSWORD_RETYPE': True,
    'USERNAME_CHANGED_EMAIL_CONFIRMATION': True,
    'PASSWORD_CHANGED_EMAIL_CONFIRMATION': True,
    'SEND_CONFIRMATION_EMAIL': True,
    'SET_USERNAME_RETYPE': True,
    'PASSWORD_RESET_CONFIRM_URL': 'password/reset/confirm/{uid}/{token}',
    'SET_PASSWORD_RETYPE': True,
    'PASSWORD_RESET_CONFIRM_RETYPE': True,
    'USERNAME_RESET_CONFIRM_URL': 'email/reset/confirm/{uid}/{token}',
    'ACTIVATION_URL': 'activate/{uid}/{token}',
    'SEND_ACTIVATION_EMAIL': True,
    'SOCIAL_AUTH_TOKEN_STRATEGY': 'djoser.social.token.jwt.TokenStrategy',
    'SOCIAL_AUTH_ALLOWED_REDIRECT_URIS': [
        'http://localhost:8000/google', 
        'http://localhost:8000/facebook'
        'https://fullpcstore.com/google',
        'https://fullpcstore.com/facebook',
        ],
    'SERIALIZERS': {
        'user_create': 'apps.user.serializers.UserCreateSerializer',
        'user': 'apps.user.serializers.UserCreateSerializer',
        'current_user': 'apps.user.serializers.UserCreateSerializer',
        'user_delete': 'djoser.serializers.UserDeleteSerializer',
    },
}

BT_ENVIRONMENT = os.environ.get('BT_ENVIRONMENT')
BT_MERCHANT_ID = os.environ.get('BT_MERCHANT_ID')
BT_PUBLIC_KEY = os.environ.get('BT_PUBLIC_KEY')
BT_PRIVATE_KEY = os.environ.get('BT_PRIVATE_KEY')

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

AUTH_USER_MODEL = "user.UserAccount"

if not DEBUG:
    DEFAULT_FROM_EMAIL = 'example - FULL PC TECHNOLOGY <mail@example.com>'
    EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env('EMAIL_HOST')
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
    EMAIL_PORT = env('EMAIL_PORT')
    EMAIL_USE_TLS = env('EMAIL_USE_TLS')

    # # django-ckeditor will not work with S3 through django-storages without this line in settings.py
    # AWS_QUERYSTRING_AUTH = False

    # # aws settings

    # AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    # AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    # AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')

    # AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    # AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    # AWS_DEFAULT_ACL = 'public-read'

    # # s3 static settings
    # STATIC_LOCATION = 'static'
    # STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/'
    # STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    # # s3 public media settings

    # PUBLIC_MEDIA_LOCATION = 'media'
    # MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/'
    # DEFAULT_FILE_STORAGE = 'core.storage_backends.MediaStore'

    # STATICFILES_DIRS = (os.path.join(BASE_DIR, 'build/static'),)
    # STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
