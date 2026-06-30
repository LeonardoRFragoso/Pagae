from django.contrib import admin

from .models import Merchant, MerchantApiKey


class ApiKeyInline(admin.TabularInline):
    model = MerchantApiKey
    extra = 0
    readonly_fields = ("id", "key_prefix", "environment", "is_active", "last_used", "created_at")
    fields = ("key_prefix", "name", "environment", "is_active", "last_used", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ("trade_name", "legal_name", "cnpj_masked", "status", "mdr_rate", "created_at")
    list_filter = ("status",)
    search_fields = ("legal_name", "trade_name", "cnpj", "email")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = [ApiKeyInline]

    fieldsets = (
        ("Identity", {"fields": ("id", "user", "legal_name", "trade_name", "cnpj", "email", "phone", "website")}),
        ("Settlement", {"fields": ("pix_key", "bank_code", "bank_agency", "bank_account", "bank_account_type")}),
        ("Commercial", {"fields": ("mdr_rate", "settlement_days")}),
        ("Status", {"fields": ("status", "approved_at")}),
        ("Webhook", {"fields": ("webhook_url", "webhook_secret")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="CNPJ")
    def cnpj_masked(self, obj: Merchant) -> str:
        cnpj = obj.cnpj
        return f"{cnpj[:2]}.***.***/{cnpj[8:12]}-{cnpj[12:]}" if len(cnpj) == 14 else cnpj


@admin.register(MerchantApiKey)
class MerchantApiKeyAdmin(admin.ModelAdmin):
    list_display = ("key_prefix", "merchant", "name", "environment", "is_active", "last_used", "created_at")
    list_filter = ("environment", "is_active")
    search_fields = ("key_prefix", "merchant__legal_name")
    readonly_fields = ("id", "key_prefix", "key_hash", "created_at")
    ordering = ("-created_at",)
