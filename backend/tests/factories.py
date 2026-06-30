import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import User, UserRole
from apps.customers.models import Customer, KYCStatus, RiskTier
from apps.merchants.models import Merchant, MerchantApiKey, MerchantStatus


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    phone = factory.Sequence(lambda n: f"+5511999{n:05d}")
    role = UserRole.CUSTOMER
    is_active = True
    is_staff = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "testpass123")
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, password=password, **kwargs)


class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = Customer

    user = factory.SubFactory(UserFactory, role=UserRole.CUSTOMER)
    cpf = factory.Sequence(lambda n: f"{n:011d}")
    full_name = factory.Faker("name", locale="pt_BR")
    birth_date = factory.Faker("date_of_birth", minimum_age=18, maximum_age=70)
    phone = factory.Sequence(lambda n: f"+5511988{n:05d}")
    email = factory.LazyAttribute(lambda obj: obj.user.email)
    city = "São Paulo"
    state = "SP"
    kyc_status = KYCStatus.PENDING
    risk_tier = RiskTier.NEW
    approved_limit = 0
    used_limit = 0
    is_blocked = False


class ApprovedCustomerFactory(CustomerFactory):
    kyc_status = KYCStatus.APPROVED
    risk_tier = RiskTier.LOW
    approved_limit = 50000  # R$500
    serasa_score = 650
    cpf = "12345678909"  # deterministic: stub bureau score 554, no negative record


class MerchantFactory(DjangoModelFactory):
    class Meta:
        model = Merchant

    user = factory.SubFactory(UserFactory, role=UserRole.MERCHANT_OWNER)
    legal_name = factory.Faker("company", locale="pt_BR")
    trade_name = factory.LazyAttribute(lambda obj: obj.legal_name)
    cnpj = factory.Sequence(lambda n: f"{n:014d}")
    email = factory.LazyAttribute(lambda obj: obj.user.email)
    phone = factory.Sequence(lambda n: f"+5511333{n:05d}")
    pix_key = factory.Sequence(lambda n: f"merchant{n}@pagae.com.br")
    status = MerchantStatus.ACTIVE
    mdr_rate = "0.0700"


class MerchantApiKeyFactory(DjangoModelFactory):
    class Meta:
        model = MerchantApiKey

    merchant = factory.SubFactory(MerchantFactory)
    key_prefix = factory.Sequence(lambda n: f"pk_live_{n:08d}")
    key_hash = factory.Sequence(lambda n: f"hash{n:064d}")
    name = "Test Key"
    environment = "production"
    is_active = True
