from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401, F403
from .base import Csv  # noqa: F401

DEBUG = False

# Staging keeps the sandbox provider as default. Celcoin is only allowed when
# the required credentials are explicitly provided.
PAYMENT_PROVIDER: str = config("PAYMENT_PROVIDER", default="sandbox")  # noqa: F405

if PAYMENT_PROVIDER == "celcoin" and not all(
    [CELCOIN_CLIENT_ID, CELCOIN_CLIENT_SECRET, CELCOIN_BASE_URL]  # noqa: F405
):
    raise ImproperlyConfigured(
        "PAYMENT_PROVIDER=celcoin requires CELCOIN_CLIENT_ID, "
        "CELCOIN_CLIENT_SECRET and CELCOIN_BASE_URL."
    )

# Security headers. For Railway/Vercel traffic, enable proxy headers so that
# Django sees the original HTTPS scheme.
USE_X_FORWARDED_HOST = config("USE_X_FORWARDED_HOST", cast=bool, default=True)  # noqa: F405
USE_X_FORWARDED_SSL = config("USE_X_FORWARDED_SSL", cast=bool, default=True)  # noqa: F405
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https") if USE_X_FORWARDED_SSL else None
)

SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", cast=bool, default=False)  # noqa: F405
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", cast=int, default=0)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(  # noqa: F405
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", cast=bool, default=False
)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", cast=bool, default=False)  # noqa: F405
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", cast=bool, default=True)  # noqa: F405
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", cast=bool, default=True)  # noqa: F405
X_FRAME_OPTIONS = "DENY"

# Production/staging sanity checks.
if not SECRET_KEY:  # noqa: F405
    raise ImproperlyConfigured("SECRET_KEY is required in staging.")

if not ALLOWED_HOSTS or ALLOWED_HOSTS == ["localhost"]:  # noqa: F405
    raise ImproperlyConfigured("ALLOWED_HOSTS must be configured for staging.")

# CORS: never allow all origins in staging.
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config(  # noqa: F405
    "CORS_ALLOWED_ORIGINS", cast=Csv(), default=""  # noqa: F405
)
if not CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS is required in staging.")

CSRF_TRUSTED_ORIGINS = config(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS", cast=Csv(), default=",".join(CORS_ALLOWED_ORIGINS)
)

# Throttling is enabled in staging.
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [  # noqa: F405
    "core.throttling.IPScopedRateThrottle"
]

# Static/media served locally in staging (production may use S3).
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": str(MEDIA_ROOT)},  # noqa: F405
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Email defaults to console in staging unless SMTP is configured.
EMAIL_BACKEND = config(  # noqa: F405
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
