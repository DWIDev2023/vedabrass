from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-qg9l1lu9vakaszr@hug63#t^fik6f%#2$&79@ajzd(%vg0_#6d'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = [
    'django_sonar',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'daphne',
    'channels',
    'django.contrib.humanize',
    "django.contrib.sitemaps",

    'core',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'core.middleware.CustomErrorMiddleware',
]

AUTH_USER_MODEL="core.User"

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES':{
        'connect.authentication.APIKeyAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    },
    'DEFAULT_PERMISSION_CLASSES':{
        'rest_framework.permissions.IsAuthenticated',
    },
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'vedabrass.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "core.context_processors.menu_collections",
                "core.context_processors.cart_data",
                "core.context_processors.canonical_url",
                "core.context_processors.page_faqs",
            ],
        },
    },
]

ASGI_APPLICATION = 'vedabrass.asgi.application'
WSGI_APPLICATION = 'vedabrass.wsgi.application'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static/"),
]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DJANGO_SONAR = {
    'excludes': [
        STATIC_URL,
        MEDIA_URL,
        '/sonar/',
        '/admin/',
        '/__reload__/',
    ],
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS').lower() == 'true'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

ORDER_ADMIN_EMAILS = [
    email.strip()
    for email in os.getenv(
        "ORDER_ADMIN_EMAILS",
        "orders@vedabrass.com"
    ).split(",")
]

GOOGLE_MAPS_API_KEY= os.environ.get("GOOGLE_MAPS_API_KEY")

PAYU_KEY = os.getenv("PAYU_KEY")
PAYU_SALT = os.getenv("PAYU_SALT")
PAYU_BASE_URL = os.getenv("PAYU_BASE_URL")

SHIPROCKET_EMAIL = os.getenv("SHIPROCKET_EMAIL")
SHIPROCKET_PASSWORD = os.getenv("SHIPROCKET_PASSWORD")
SHIPROCKET_BASE_URL = os.getenv("SHIPROCKET_BASE_URL")
SHIPROCKET_PICKUP_LOCATION = os.getenv("SHIPROCKET_PICKUP_LOCATION", "Primary")

WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "False") == "True"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_LANGUAGE_CODE = os.getenv("WHATSAPP_LANGUAGE_CODE", "en")

WHATSAPP_ORDER_PAID_TEMPLATE = os.getenv("WHATSAPP_ORDER_PAID_TEMPLATE")
WHATSAPP_TRACKING_TEMPLATE = os.getenv("WHATSAPP_TRACKING_TEMPLATE")
WHATSAPP_ORDER_CANCELLED_TEMPLATE = os.getenv("WHATSAPP_ORDER_CANCELLED_TEMPLATE")
WHATSAPP_PAYMENT_ABANDONED_TEMPLATE = os.getenv("WHATSAPP_PAYMENT_ABANDONED_TEMPLATE")

SMS_ENABLED = os.getenv("SMS_ENABLED", "False") == "True"
SMS_API_URL = os.getenv("SMS_API_URL")
SMS_API_KEY = os.getenv("SMS_API_KEY")
SMS_SENDER_ID = os.getenv("SMS_SENDER_ID")
SMS_ROUTE_ID = os.getenv("SMS_ROUTE_ID", "13")
SMS_CAMPAIGN = os.getenv("SMS_CAMPAIGN", "0")

