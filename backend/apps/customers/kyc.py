"""
KYC provider abstraction layer.

Phase 1: Interface + stub implementation only.
Phase 2: Wire CAF.io adapter here.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass
class KYCResult:
    success: bool
    provider_id: str
    status: str  # approved | rejected | pending | manual_review
    reason: str | None = None
    raw_response: dict = field(default_factory=dict)


class KYCProvider(ABC):
    """Abstract interface for KYC document and identity verification providers."""

    @abstractmethod
    def validate_cpf(self, cpf: str, full_name: str, birth_date: date) -> KYCResult:
        """Validate CPF against bureau data. Returns match result."""
        ...

    @abstractmethod
    def validate_document(self, document_front: bytes, document_back: bytes, document_type: str) -> KYCResult:
        """OCR and validate a government-issued identity document."""
        ...

    @abstractmethod
    def validate_selfie(self, selfie: bytes, document_front: bytes) -> KYCResult:
        """Liveness check and face match against document photo."""
        ...


class StubKYCProvider(KYCProvider):
    """
    Stub implementation for development and testing.
    Always returns approved. Replace with CAFProvider in Phase 2.
    """

    def validate_cpf(self, cpf: str, full_name: str, birth_date: date) -> KYCResult:
        return KYCResult(success=True, provider_id=f"stub-cpf-{cpf[-4:]}", status="approved")

    def validate_document(self, document_front: bytes, document_back: bytes, document_type: str) -> KYCResult:
        return KYCResult(success=True, provider_id="stub-doc-001", status="approved")

    def validate_selfie(self, selfie: bytes, document_front: bytes) -> KYCResult:
        return KYCResult(success=True, provider_id="stub-selfie-001", status="approved")


def get_kyc_provider() -> KYCProvider:
    """
    Factory: return the active KYC provider based on settings.
    Phase 2: switch to CAFProvider when CAF_API_KEY is configured.
    """
    from django.conf import settings

    if getattr(settings, "CAF_API_KEY", ""):
        # Phase 2: from integrations.caf import CAFProvider; return CAFProvider()
        raise NotImplementedError("CAFProvider not yet implemented. Coming in Phase 2.")

    return StubKYCProvider()
