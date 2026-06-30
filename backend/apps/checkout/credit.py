from dataclasses import dataclass, field
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
    reasons: list[str] = field(default_factory=list)
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
        reasons: list[str] = []

        # 1. KYC
        if not customer.is_kyc_approved:
            reasons.append("kyc_not_approved")
            return CreditDecision(result="deny", reason=reasons[0], reasons=reasons)

        reasons.append("kyc_approved")

        # 2. Blocked
        if customer.is_blocked:
            reasons.append("customer_blocked")
            return CreditDecision(result="deny", reason=reasons[-1], reasons=reasons)

        # 3. CPF / phone presence
        if not customer.cpf:
            reasons.append("missing_cpf")
            return CreditDecision(result="deny", reason=reasons[-1], reasons=reasons)
        if not customer.phone:
            reasons.append("missing_phone")
            return CreditDecision(result="deny", reason=reasons[-1], reasons=reasons)

        # 4. Velocity
        velocity_key = f"credit:velocity:{customer.cpf}"
        try:
            applications_today = cache.incr(velocity_key, delta=1)
        except ValueError:
            cache.set(velocity_key, 1, timeout=86_400)
            applications_today = 1
        if applications_today > _MAX_APPLICATIONS_PER_DAY:
            reasons.append("velocity_exceeded")
            return CreditDecision(result="deny", reason=reasons[-1], reasons=reasons)

        # 5. Bureau check
        bureau = self.bureau_client.check(customer.cpf)
        if bureau.has_active_negative:
            reasons.append("negative_record")
            return CreditDecision(result="deny", reason=reasons[-1], score=bureau.score, reasons=reasons)

        # 6. Score-based limit
        approved_limit = next(
            (limit for score, limit in _LIMITS_BY_SCORE if bureau.score >= score),
            0,
        )
        if approved_limit == 0:
            reasons.append("low_score")
            return CreditDecision(result="deny", reason=reasons[-1], score=bureau.score, reasons=reasons)

        reasons.append(f"score_ok:{bureau.score}")

        # 7. Amount check
        if amount_cents > approved_limit:
            reasons.append("amount_exceeds_limit")
            return CreditDecision(
                result="deny",
                reason=reasons[-1],
                score=bureau.score,
                approved_limit=approved_limit,
                reasons=reasons,
            )

        if amount_cents > customer.available_limit:
            reasons.append("insufficient_limit")
            return CreditDecision(
                result="deny",
                reason=reasons[-1],
                score=bureau.score,
                approved_limit=approved_limit,
                reasons=reasons,
            )

        reasons.append("approved")
        return CreditDecision(
            result="approve",
            reason=reasons[-1],
            reasons=reasons,
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
