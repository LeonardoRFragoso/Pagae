import logging

from django.conf import settings
from django.db import connection
from django_redis import get_redis_connection
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """Public health endpoint used by load balancers and deploy checklists."""

    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request: Request) -> Response:
        database_ok = True
        redis_ok = True

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            database_ok = False
            logger.exception("healthcheck_db_failed")

        try:
            redis = get_redis_connection("default")
            redis.ping()
        except Exception:
            redis_ok = False
            logger.exception("healthcheck_redis_failed")

        healthy = database_ok and redis_ok
        data = {
            "status": "ok" if healthy else "degraded",
            "database": "ok" if database_ok else "error",
            "redis": "ok" if redis_ok else "error",
            "payment_provider": settings.PAYMENT_PROVIDER,
            "version": settings.VERSION,
        }
        return Response(data, status=200 if healthy else 503)
