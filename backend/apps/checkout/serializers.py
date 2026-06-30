from rest_framework import serializers

from apps.customers.models import Customer


class CustomerIdentifierSerializer(serializers.Serializer):
    cpf = serializers.CharField(max_length=14, required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20, required=False)


class CheckoutCreateSerializer(serializers.Serializer):
    merchant_order_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    customer = CustomerIdentifierSerializer()
    total_amount = serializers.IntegerField(min_value=100)  # min R$1,00
    installment_count = serializers.IntegerField(min_value=1, max_value=12)

    def validate(self, data: dict) -> dict:
        customer = data.get("customer", {})
        if not any(customer.get(k) for k in ("cpf", "email", "phone")):
            raise serializers.ValidationError("At least one customer identifier (cpf, email or phone) is required.")
        return data


class InstallmentScheduleSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    amount = serializers.IntegerField()
    due_date = serializers.DateField()


class CheckoutSerializer(serializers.Serializer):
    id = serializers.UUIDField()
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
