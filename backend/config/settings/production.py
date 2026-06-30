import sentry_sdk
from django.core.exceptions import ImproperlyConfigured
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa: F401, F403
from .base import Csv  # noqa: F401

DEBUG = False

# Production keeps sandbox as default until Celcoin credentials are explicitly
# configured and the integration is validated.
PAYMENT_PROVIDER: str = config("PAYMENT_PROVIDER", default="sandbox")  # noqa: F405

if PAYMENT_PROVIDER == "celcoin" and not all(
    [CELCOIN_CLIENT_ID, CELCOIN_CLIENT_SECRET, CELCOIN_BASE_URL]  # noqa: F405
):
    raise ImproperlyConfigured(
        "PAYMENT_PROVIDER=celcoin requires CELCOIN_CLIENT_ID, "
        "CELCOIN_CLIENT_SECRET and CELCOIN_BASE_URL."
    )

# Trust proxy headers from Railway/Vercel front-end load balancers.
USE_X_FORWARDED_HOST = config("USE_X_FORWARDED_HOST", cast=bool, default=True)  # noqa: F405
USE_X_FORWARDED_SSL = config("USE_X_FORWARDED_SSL", cast=bool, default=True)  # noqa: F405
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https") if USE_X_FORWARDED_SSL else None
)

SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", cast=bool, default=True)  # noqa: F405
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", cast=int, default=31536000)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(  # noqa: F405
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", cast=bool, default=True
)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", cast=bool, default=True)  # noqa: F405
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", cast=bool, default=True)  # noqa: F405
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", cast=bool, default=True)  # noqa: F405
X_FRAME_OPTIONS = "DENY"

# Production sanity checks.
if not SECRET_KEY:  # noqa: F405
    raise ImproperlyConfigured("SECRET_KEY is required in production.")

if not ALLOWED_HOSTS or ALLOWED_HOSTS == ["localhost"]:  # noqa: F405
    raise ImproperlyConfigured("ALLOWED_HOSTS must be configured for production.")

# CORS: never allow all origins in production.
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config(  # noqa: F405
    "CORS_ALLOWED_ORIGINS", cast=Csv(), default=""  # noqa: F405
)
if not CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS is required in production.")

CSRF_TRUSTED_ORIGINS = config(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS", cast=Csv(), default=",".join(CORS_ALLOWED_ORIGINS)
)

# Throttling is enabled in production.
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [  # noqa: F405
    "core.throttling.IPScopedRateThrottle"
]

# Media files go to S3 when credentials are configured; otherwise keep local.
_aws_bucket_name = config("AWS_STORAGE_BUCKET_NAME", default="")  # noqa: F405
if _aws_bucket_name:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "bucket_name": _aws_bucket_name,
                "region_name": config("AWS_S3_REGION_NAME", default="sa-east-1"),  # noqa: F405
                "default_acl": "private",
                "file_overwrite": False,
                "object_parameters": {"ServerSideEncryption": "AES256"},
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

_sentry_dsn = config("SENTRY_DSN", default="")  # noqa: F405
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[
            DjangoIntegration(transaction_style="url"),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
