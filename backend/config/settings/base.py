from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY: str = config("SECRET_KEY")

ALLOWED_HOSTS: list[str] = config("ALLOWED_HOSTS", cast=Csv(), default="localhost")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.customers",
    "apps.merchants",
    "apps.checkout",
    "apps.payments",
    "apps.settlements",
    "apps.ledger",
    "apps.webhooks",
    "apps.notifications",
    "apps.collections",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.CorrelationIdMiddleware",
    "core.middleware.RequestLoggingMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="pagae"),
        "USER": config("DB_USER", default="pagae"),
        "PASSWORD": config("DB_PASSWORD", default="pagae"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "OPTIONS": {
            "connect_timeout": 10,
        },
        "CONN_MAX_AGE": 60,
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://localhost:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "apps.merchants.authentication.ApiKeyAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardResultsPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", cast=int, default=15)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_TOKEN_LIFETIME_DAYS", cast=int, default=7)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "apps.accounts.serializers.CustomTokenObtainPairSerializer",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Pagaê API",
    "DESCRIPTION": "Brazilian BNPL Platform — MVP",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

CELERY_BROKER_URL: str = config("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND: str = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Sao_Paulo"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BEAT_SCHEDULE: dict = {
    "collections-daily-overdue-check": {
        "task": "collections.run_daily_overdue_check",
        "schedule": crontab(hour=8, minute=0),
        "options": {"expires": 3600},
    },
    "collections-due-soon-reminders": {
        "task": "collections.run_due_soon_reminders",
        "schedule": crontab(hour=9, minute=0),
        "options": {"expires": 3600},
    },
}

CORS_ALLOWED_ORIGINS: list[str] = config("CORS_ALLOWED_ORIGINS", cast=Csv(), default="http://localhost:5173")

OTP_TTL_SECONDS: int = config("OTP_TTL_SECONDS", cast=int, default=300)
OTP_MAX_ATTEMPTS: int = config("OTP_MAX_ATTEMPTS", cast=int, default=3)

CELCOIN_CLIENT_ID: str = config("CELCOIN_CLIENT_ID", default="")
CELCOIN_CLIENT_SECRET: str = config("CELCOIN_CLIENT_SECRET", default="")
CELCOIN_BASE_URL: str = config("CELCOIN_BASE_URL", default="https://sandbox.openfinance.celcoin.dev")

SERASA_API_KEY: str = config("SERASA_API_KEY", default="")
SERASA_BASE_URL: str = config("SERASA_BASE_URL", default="")

CAF_API_KEY: str = config("CAF_API_KEY", default="")
CAF_BASE_URL: str = config("CAF_BASE_URL", default="")

ZAPI_INSTANCE_ID: str = config("ZAPI_INSTANCE_ID", default="")
ZAPI_TOKEN: str = config("ZAPI_TOKEN", default="")
ZAPI_BASE_URL: str = config("ZAPI_BASE_URL", default="https://api.z-api.io")

BREVO_API_KEY: str = config("BREVO_API_KEY", default="")
DEFAULT_FROM_EMAIL: str = config("DEFAULT_FROM_EMAIL", default="noreply@pagae.com.br")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "core.logging.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
