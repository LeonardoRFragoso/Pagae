from .base import *  # noqa: F401, F403

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "pagae_test",
        "USER": "pagae",
        "PASSWORD": "pagae",
        "HOST": "localhost",
        "PORT": "15432",
        "TEST": {
            "NAME": "pagae_test",
        },
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

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CELCOIN_BASE_URL = "https://sandbox.openfinance.celcoin.dev"
SERASA_BASE_URL = "https://sandbox.serasa.com.br"
CAF_BASE_URL = "https://sandbox.caf.io"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
