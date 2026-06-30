import logging
import random
import string
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache

from core.exceptions import ConflictError, ValidationError

if TYPE_CHECKING:
    from .models import User as UserType

logger = logging.getLogger(__name__)
User = get_user_model()

OTP_PREFIX = "otp:"
OTP_ATTEMPT_PREFIX = "otp_attempts:"


class AccountService:
    def register(self, email: str, password: str, phone: str = "", role: str = "customer") -> "UserType":
        email = email.lower().strip()
        if User.objects.filter(email=email).exists():
            raise ConflictError("A user with this email already exists.", "email_taken")

        user = User.objects.create_user(email=email, password=password, phone=phone, role=role)
        logger.info("user_registered", extra={"user_id": str(user.id), "role": role})
        return user

    def generate_otp(self, phone: str) -> str:
        """Generate a 6-digit OTP, store in Redis with TTL."""
        otp = "".join(random.choices(string.digits, k=6))
        ttl = getattr(settings, "OTP_TTL_SECONDS", 300)
        cache.set(f"{OTP_PREFIX}{phone}", otp, timeout=ttl)
        cache.set(f"{OTP_ATTEMPT_PREFIX}{phone}", 0, timeout=ttl)
        logger.info("otp_generated", extra={"phone": phone[-4:]})
        return otp

    def verify_otp(self, phone: str, otp: str) -> bool:
        """Verify OTP. Increments attempt counter; invalidates after max attempts."""
        max_attempts = getattr(settings, "OTP_MAX_ATTEMPTS", 3)
        attempts_key = f"{OTP_ATTEMPT_PREFIX}{phone}"
        stored_otp = cache.get(f"{OTP_PREFIX}{phone}")

        if stored_otp is None:
            raise ValidationError("OTP expired or not found.", "otp_expired")

        attempts = cache.get(attempts_key, 0)
        if attempts >= max_attempts:
            cache.delete(f"{OTP_PREFIX}{phone}")
            raise ValidationError("Too many incorrect attempts. Request a new OTP.", "otp_max_attempts")

        if stored_otp != otp:
            cache.incr(attempts_key)
            raise ValidationError("Invalid OTP.", "otp_invalid")

        cache.delete(f"{OTP_PREFIX}{phone}")
        cache.delete(attempts_key)
        return True
