import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from tests.factories import CustomerFactory, MerchantFactory, UserFactory


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def customer_user():
    return UserFactory(role="customer")


@pytest.fixture
def merchant_user():
    return UserFactory(role="merchant_owner")


@pytest.fixture
def ops_user():
    return UserFactory(role="ops")


@pytest.fixture
def admin_user():
    return UserFactory(role="admin", is_staff=True, is_superuser=True)


@pytest.fixture
def customer_user_client(api_client, customer_user) -> APIClient:
    api_client.force_authenticate(user=customer_user)
    return api_client


@pytest.fixture
def merchant_user_client(api_client, merchant_user) -> APIClient:
    api_client.force_authenticate(user=merchant_user)
    return api_client


@pytest.fixture
def customer(customer_user):
    return CustomerFactory(user=customer_user)


@pytest.fixture
def merchant(merchant_user):
    return MerchantFactory(user=merchant_user)
