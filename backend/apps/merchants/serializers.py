import re

from rest_framework import serializers

from apps.checkout.models import CheckoutSession
from apps.settlements.models import Settlement

from .models import Merchant, MerchantApiKey


def _validate_cnpj(cnpj: str) -> str:
    cnpj = re.sub(r"\D", "", cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        raise serializers.ValidationError("Invalid CNPJ.")

    def calc_digit(cnpj: str, weights: list[int]) -> int:
        total = sum(int(d) * w for d, w in zip(cnpj, weights, strict=False))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    if int(cnpj[12]) != calc_digit(cnpj[:12], w1):
        raise serializers.ValidationError("Invalid CNPJ.")
    if int(cnpj[13]) != calc_digit(cnpj[:13], w2):
        raise serializers.ValidationError("Invalid CNPJ.")
    return cnpj


class MerchantCreateSerializer(serializers.ModelSerializer):
    cnpj = serializers.CharField(max_length=18)

    class Meta:
        model = Merchant
        fields = (
            "legal_name",
            "trade_name",
            "cnpj",
            "email",
            "phone",
            "website",
            "pix_key",
        )

    def validate_cnpj(self, value: str) -> str:
        return _validate_cnpj(value)


class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = (
            "id",
            "legal_name",
            "trade_name",
            "cnpj",
            "email",
            "phone",
            "website",
            "pix_key",
            "mdr_rate",
            "settlement_days",
            "status",
            "webhook_url",
            "created_at",
        )
        read_only_fields = fields


class ApiKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False, default="")
    environment = serializers.ChoiceField(choices=["sandbox", "production"], default="production")


class ApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantApiKey
        fields = ("id", "key_prefix", "name", "environment", "is_active", "last_used", "created_at")
        read_only_fields = fields


class ApiKeyCreatedSerializer(serializers.ModelSerializer):
    """Returned only once at creation — includes the full key."""
    full_key = serializers.CharField(read_only=True)

    class Meta:
        model = MerchantApiKey
        fields = ("id", "key_prefix", "full_key", "name", "environment", "created_at")
        read_only_fields = fields


class MerchantDashboardSerializer(serializers.Serializer):
    gmv_today = serializers.IntegerField()
    gmv_week = serializers.IntegerField()
    gmv_month = serializers.IntegerField()
    approval_rate = serializers.FloatField()
    total_transactions = serializers.IntegerField()
    pending_settlement = serializers.IntegerField()


class MerchantTransactionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    customer_cpf = serializers.CharField(source="customer.cpf", read_only=True)

    class Meta:
        model = CheckoutSession
        fields = (
            "id",
            "merchant_order_id",
            "customer_name",
            "customer_cpf",
            "total_amount",
            "net_amount",
            "installment_count",
            "status",
            "created_at",
        )
        read_only_fields = fields


class MerchantTransactionDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    customer_cpf = serializers.CharField(source="customer.cpf", read_only=True)
    installments = serializers.SerializerMethodField()

    class Meta:
        model = CheckoutSession
        fields = (
            "id",
            "merchant_order_id",
            "customer_name",
            "customer_cpf",
            "total_amount",
            "net_amount",
            "installment_count",
            "status",
            "decision",
            "settled_at",
            "installments",
            "created_at",
        )
        read_only_fields = fields

    def get_installments(self, obj: CheckoutSession) -> list[dict]:
        return [
            {
                "id": str(i.id),
                "number": i.number,
                "amount": i.amount,
                "due_date": i.due_date,
                "status": i.status,
                "paid_at": i.paid_at,
                "days_past_due": i.days_past_due,
            }
            for i in obj.installments.all().order_by("number")
        ]


class MerchantSettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settlement
        fields = (
            "id",
            "amount",
            "period_start",
            "period_end",
            "status",
            "pix_e2e_id",
            "paid_at",
            "failure_reason",
            "created_at",
        )
        read_only_fields = fields


class MerchantWebhookUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = ("webhook_url", "webhook_secret")
