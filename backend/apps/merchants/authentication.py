from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

_BEARER_PREFIX = "Bearer "
_API_KEY_PREFIX_TAGS = ("pk_live_", "pk_test_")


class ApiKeyAuthentication(BaseAuthentication):
    """
    Authenticate merchant API requests via the Authorization header.

    Header format:  Authorization: Bearer pk_live_<key>
    """

    def authenticate(self, request: Request):
        # Import service locally to avoid a circular import at DRF settings load time.
        from .services import MerchantService

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith(_BEARER_PREFIX):
            return None

        full_key = auth_header[len(_BEARER_PREFIX):].strip()
        if not any(full_key.startswith(tag) for tag in _API_KEY_PREFIX_TAGS):
            return None

        service = MerchantService()
        api_key = service.verify_api_key(full_key)
        if api_key is None:
            raise AuthenticationFailed("Invalid or inactive API key.")

        return (api_key.merchant.user, api_key)

    def authenticate_header(self, request: Request) -> str:
        return "Bearer"
