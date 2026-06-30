"""Rate-limiting throttles keyed by IP address for sensitive public endpoints."""

from rest_framework.throttling import ScopedRateThrottle


class IPScopedRateThrottle(ScopedRateThrottle):
    """
    ScopedRateThrottle that always uses the client IP as the cache key,
    regardless of authentication state. Useful for login, checkout public,
    payment simulation and webhooks.
    """

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
