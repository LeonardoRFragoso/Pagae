import re
from datetime import date

from rest_framework import serializers

from .models import Customer


def _validate_cpf(cpf: str) -> str:
    """Strip formatting and validate CPF check digits."""
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise serializers.ValidationError("Invalid CPF.")

    for i in range(2):
        total = sum(int(cpf[j]) * (10 + i - j) for j in range(9 + i))
        digit = (total * 10 % 11) % 10
        if digit != int(cpf[9 + i]):
            raise serializers.ValidationError("Invalid CPF.")
    return cpf


class CustomerCreateSerializer(serializers.ModelSerializer):
    cpf = serializers.CharField(max_length=14)
    birth_date = serializers.DateField()

    class Meta:
        model = Customer
        fields = (
            "cpf",
            "full_name",
            "birth_date",
            "phone",
            "email",
            "cep",
            "street",
            "number",
            "complement",
            "neighborhood",
            "city",
            "state",
        )

    def validate_cpf(self, value: str) -> str:
        return _validate_cpf(value)

    def validate_birth_date(self, value: date) -> date:
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise serializers.ValidationError("Customer must be at least 18 years old.")
        if age > 120:
            raise serializers.ValidationError("Invalid birth date.")
        return value


class CustomerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("phone", "email", "cep", "street", "number", "complement", "neighborhood", "city", "state")


class CustomerSerializer(serializers.ModelSerializer):
    available_limit = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = (
            "id",
            "cpf",
            "full_name",
            "birth_date",
            "phone",
            "email",
            "cep",
            "street",
            "number",
            "complement",
            "neighborhood",
            "city",
            "state",
            "kyc_status",
            "risk_tier",
            "approved_limit",
            "used_limit",
            "available_limit",
            "is_blocked",
            "created_at",
        )
        read_only_fields = fields
