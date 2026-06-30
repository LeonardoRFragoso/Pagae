"""Provider-agnostic payment abstraction layer.

This module defines the interface used by the payments app to create charges,
receive webhooks and send payouts. New providers (Asaas, Mercado Pago, Efí,
Iugu, OpenPix, etc.) can be added without changing the core business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from django.conf import settings

from integrations.celcoin import CelcoinClient


@dataclass(frozen=True)
class ChargeResult:
    """Result of creating a payment charge."""

    provider_transaction_id: str
    txid: str
    qr_code: str
    pix_code: str
    expires_at: datetime


class PaymentProvider(ABC):
    """Abstract base class for any payment gateway."""

    name: str = ""

    @abstractmethod
    def create_charge(
        self,
        amount_cents: int,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ChargeResult:
        """Create a charge and return its public identifiers."""

    @abstractmethod
    def parse_webhook(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Parse a provider-specific webhook into a normalized dict."""

    @abstractmethod
    def payout(self, pix_key: str, amount_cents: int, description: str) -> dict[str, Any]:
        """Send a payout to the merchant."""


class SandboxProvider(PaymentProvider):
    """Fake provider used for development and end-to-end tests."""

    name = "sandbox"

    def create_charge(
        self,
        amount_cents: int,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ChargeResult:
        provider_transaction_id = f"SANDBOX-{uuid4().hex[:16].upper()}"
        txid = str(uuid4()).replace("-", "")[:35]
        qr_code = (
            f"00020126430014BR.GOV.BCB.PIX0117{provider_transaction_id}"
            f"520400005303986540{amount_cents:010d}5802BR5910Pagaê6009SaoPaulo"
        )
        pix_code = f"pix:{provider_transaction_id}"
        expires_at = datetime.now(UTC) + timedelta(minutes=30)
        return ChargeResult(
            provider_transaction_id=provider_transaction_id,
            txid=txid,
            qr_code=qr_code,
            pix_code=pix_code,
            expires_at=expires_at,
        )

    def parse_webhook(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        txid = payload.get("txid") or payload.get("endToEndId")
        if not txid:
            return None
        return {
            "txid": txid,
            "amount_cents": int(payload.get("amount", 0) * 100),
            "paid_at": payload.get("paid_at") or payload.get("paidAt"),
            "payer_name": payload.get("payer", {}).get("name", ""),
            "payer_cpf": payload.get("payer", {}).get("cpf", ""),
            "status": "paid",
        }

    def payout(self, pix_key: str, amount_cents: int, description: str) -> dict[str, Any]:
        if not pix_key:
            return {"status": "failed", "failure_reason": "missing_pix_key"}
        e2e_id = f"E2E{uuid4().hex[:16].upper()}"
        return {"e2e_id": e2e_id, "status": "completed"}


class CelcoinProvider(PaymentProvider):
    """Production-oriented adapter around the Celcoin client."""

    name = "celcoin"

    def __init__(self, client: CelcoinClient | None = None) -> None:
        self.client = client or CelcoinClient()

    def create_charge(
        self,
        amount_cents: int,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ChargeResult:
        result = self.client.create_dynamic_qr(amount_cents=amount_cents, description=description)
        return ChargeResult(
            provider_transaction_id=result.celcoin_id,
            txid=result.txid,
            qr_code=result.qr_code,
            pix_code=result.pix_code,
            expires_at=result.expires_at,
        )

    def parse_webhook(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        return self.client.parse_payment_webhook(payload)

    def payout(self, pix_key: str, amount_cents: int, description: str) -> dict[str, Any]:
        return self.client.outbound_pix(pix_key, amount_cents, description)


_PROVIDER_MAP: dict[str, type[PaymentProvider]] = {
    "sandbox": SandboxProvider,
    "celcoin": CelcoinProvider,
}


def get_payment_provider() -> PaymentProvider:
    """Return the configured provider instance."""
    provider_name = getattr(settings, "PAYMENT_PROVIDER", "sandbox").lower()
    provider_class = _PROVIDER_MAP.get(provider_name, SandboxProvider)
    return provider_class()
