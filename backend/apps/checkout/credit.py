from dataclasses import dataclass
from typing import Protocol

from django.core.cache import cache

from apps.customers.models import Customer


class BureauClient(Protocol):
    def check(self, cpf: str) -> "BureauResult": ...


@dataclass(frozen=True)
class BureauResult:
    cpf: str
    score: int
    has_active_negative: bool


@dataclass(frozen=True)
class CreditDecision:
    result: str  # approve | deny
    reason: str = ""
    approved_amount: int = 0
    approved_limit: int = 0
    score: int = 0


class StubBureauClient:
    """Deterministic stub for development and tests."""

    def check(self, cpf: str) -> BureauResult:
        digits = [int(c) for c in cpf if c.isdigit()]
        score = 500 + (sum(digits) % 300)
        has_negative = digits[-1] < 2 if digits else False
        return BureauResult(cpf=cpf, score=score, has_active_negative=has_negative)


_LIMITS_BY_SCORE = [
    (700, 500_00),  # >= 700 -> R$500
    (600, 300_00),  # >= 600 -> R$300
    (500, 150_00),  # >= 500 -> R$150
    (0, 0),
]

_MAX_APPLICATIONS_PER_DAY = 2


class CreditEngine:
    def __init__(self, bureau_client: BureauClient | None = None) -> None:
        self.bureau_client = bureau_client or StubBureauClient()

    def decide(self, customer: Customer, amount_cents: int) -> CreditDecision:
        # 1. KYC
        if not customer.is_kyc_approved:
            return CreditDecision(result="deny", reason="kyc_not_approved")

        # 2. Blocked
        if customer.is_blocked:
            return CreditDecision(result="deny", reason="customer_blocked")

        # 3. Velocity
        velocity_key = f"credit:velocity:{customer.cpf}"
        try:
            applications_today = cache.incr(velocity_key, delta=1)
        except ValueError:
            cache.set(velocity_key, 1, timeout=86_400)
            applications_today = 1
        if applications_today > _MAX_APPLICATIONS_PER_DAY:
            return CreditDecision(result="deny", reason="velocity_exceeded")

        # 4. Bureau check
        bureau = self.bureau_client.check(customer.cpf)
        if bureau.has_active_negative:
            return CreditDecision(result="deny", reason="negative_record")

        # 5. Score-based limit
        approved_limit = next(
            (limit for score, limit in _LIMITS_BY_SCORE if bureau.score >= score),
            0,
        )
        if approved_limit == 0:
            return CreditDecision(result="deny", reason="low_score", score=bureau.score)

        # 6. Amount check
        if amount_cents > approved_limit:
            return CreditDecision(result="deny", reason="amount_exceeds_limit", score=bureau.score)

        if amount_cents > customer.available_limit:
            return CreditDecision(result="deny", reason="insufficient_limit", score=bureau.score)

        return CreditDecision(
            result="approve",
            approved_amount=amount_cents,
            approved_limit=approved_limit,
            score=bureau.score,
        )

    def refresh_limit(self, customer: Customer, amount_cents: int) -> None:
        """Atomically reserve the approved amount from the customer's limit."""
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE customers
                SET used_limit = used_limit + %s
                WHERE id = %s
                """,
                [amount_cents, customer.id],
            )
