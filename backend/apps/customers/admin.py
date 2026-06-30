from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "cpf_masked",
        "phone",
        "kyc_status",
        "risk_tier",
        "approved_limit_display",
        "is_blocked",
        "created_at",
    )
    list_filter = ("kyc_status", "risk_tier", "is_blocked", "state")
    search_fields = ("full_name", "cpf", "email", "phone")
    readonly_fields = ("id", "created_at", "updated_at", "available_limit")
    ordering = ("-created_at",)

    fieldsets = (
        ("Identity", {"fields": ("id", "user", "cpf", "full_name", "birth_date", "phone", "email")}),
        ("Address", {"fields": ("cep", "street", "number", "complement", "neighborhood", "city", "state")}),
        ("KYC", {"fields": ("kyc_status", "kyc_provider_id", "kyc_approved_at")}),
        (
            "Credit",
            {
                "fields": (
                    "serasa_score",
                    "risk_tier",
                    "approved_limit",
                    "used_limit",
                    "available_limit",
                    "is_blocked",
                    "blocked_reason",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="CPF")
    def cpf_masked(self, obj: Customer) -> str:
        cpf = obj.cpf.replace(".", "").replace("-", "")
        return f"***{cpf[3:9]}**" if len(cpf) == 11 else obj.cpf

    @admin.display(description="Limit (R$)")
    def approved_limit_display(self, obj: Customer) -> str:
        return f"R$ {obj.approved_limit / 100:,.2f}"
