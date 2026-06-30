from rest_framework import serializers

from apps.customers.models import Customer

from .models import Order


class CustomerIdentifierSerializer(serializers.Serializer):
    cpf = serializers.CharField(max_length=14, required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20, required=False)


class OrderCreateSerializer(serializers.Serializer):
    merchant_order_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    customer = CustomerIdentifierSerializer(required=False)
    total_amount = serializers.IntegerField(min_value=100)  # min R$1,00
    installment_count = serializers.IntegerField(min_value=1, max_value=12)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)


class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True, allow_null=True)
    customer_cpf = serializers.CharField(source="customer.cpf", read_only=True, allow_null=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "merchant_order_id",
            "customer_name",
            "customer_cpf",
            "total_amount",
            "installment_count",
            "description",
            "status",
            "expires_at",
            "created_at",
        )


class CheckoutCreateSerializer(serializers.Serializer):
    order_id = serializers.UUIDField(required=False)
    merchant_order_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    customer = CustomerIdentifierSerializer(required=False)
    total_amount = serializers.IntegerField(min_value=100, required=False)  # min R$1,00
    installment_count = serializers.IntegerField(min_value=1, max_value=12, required=False)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, data: dict) -> dict:
        if not data.get("order_id"):
            customer = data.get("customer", {})
            if not any(customer.get(k) for k in ("cpf", "email", "phone")):
                raise serializers.ValidationError(
                    "At least one customer identifier (cpf, email or phone) is required when order_id is not provided."
                )
            if data.get("total_amount") is None:
                raise serializers.ValidationError("total_amount is required when order_id is not provided.")
        return data


class InstallmentScheduleSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    amount = serializers.IntegerField()
    due_date = serializers.DateField()


class CheckoutSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    order_id = serializers.UUIDField()
    status = serializers.CharField()
    decision = serializers.CharField()
    denial_reason = serializers.CharField()
    total_amount = serializers.IntegerField()
    installment_count = serializers.IntegerField()
    installment_amount = serializers.IntegerField()
    schedule = InstallmentScheduleSerializer(many=True)
    txid = serializers.CharField(required=False)
    qr_code = serializers.CharField(required=False)
    pix_code = serializers.CharField(required=False)
    expires_at = serializers.DateTimeField()


class CustomerCheckoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "cpf", "full_name", "phone", "email")
