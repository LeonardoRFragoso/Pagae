import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class UserRole(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    MERCHANT_OWNER = "merchant_owner", "Merchant Owner"
    OPS = "ops", "Operations"
    ADMIN = "admin", "Admin"


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=30, choices=UserRole.choices, default=UserRole.CUSTOMER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"

    @property
    def is_customer(self) -> bool:
        return self.role == UserRole.CUSTOMER

    @property
    def is_merchant_owner(self) -> bool:
        return self.role == UserRole.MERCHANT_OWNER

    @property
    def is_ops(self) -> bool:
        return self.role == UserRole.OPS

    @property
    def is_admin_user(self) -> bool:
        return self.role == UserRole.ADMIN
