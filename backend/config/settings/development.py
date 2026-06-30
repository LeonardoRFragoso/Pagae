from .base import *  # noqa: F401, F403

DEBUG = True

INSTALLED_APPS += ["django_extensions"]  # noqa: F405

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INTERNAL_IPS = ["127.0.0.1"]

CORS_ALLOW_ALL_ORIGINS = True

DATABASES["default"]["PORT"] = config("DB_PORT", default="15432")  # noqa: F405
