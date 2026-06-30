from django.contrib import admin

from .models import Installment, PixCharge


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = ("id", "checkout", "number", "amount", "due_date", "status", "paid_at")
    list_filter = ("status", "due_date")
    search_fields = ("checkout__id", "customer__cpf")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(PixCharge)
class PixChargeAdmin(admin.ModelAdmin):
    list_display = ("id", "installment", "txid", "amount", "status", "expires_at", "paid_at")
    list_filter = ("status", "expires_at")
    search_fields = ("txid", "celcoin_id")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
