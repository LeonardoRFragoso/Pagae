from django.contrib import admin

from .models import LedgerEntry


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "merchant", "account", "amount", "description", "checkout", "created_at")
    list_filter = ("account", "created_at")
    search_fields = ("merchant__trade_name", "description", "reference")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
