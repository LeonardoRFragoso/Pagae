"""Z-API WhatsApp stub integration.

In production, replace the _post method with real HTTP calls to api.z-api.io.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ZAPIClient:
    def __init__(self, instance_id: str = "stub", token: str = "stub") -> None:
        self.instance_id = instance_id
        self.token = token

    def send_text(self, phone: str, message: str) -> dict[str, Any]:
        """Send a plain text WhatsApp message."""
        logger.info(
            "zapi_send_text",
            extra={"phone": phone, "message_preview": message[:60]},
        )
        return {"zaapId": f"stub-{phone}", "status": "sent", "phone": phone}

    def send_payment_reminder(self, phone: str, name: str, amount_cents: int, due_date: str) -> dict[str, Any]:
        amount_brl = amount_cents / 100
        message = (
            f"Olá {name}! 👋\n"
            f"Você tem uma parcela de *R$ {amount_brl:.2f}* vencendo em *{due_date}*.\n"
            f"Pague via Pix e evite a inadimplência. Acesse o app Pagaê para o QR Code."
        )
        return self.send_text(phone, message)

    def send_overdue_reminder(
        self, phone: str, name: str, amount_cents: int, days_past_due: int
    ) -> dict[str, Any]:
        amount_brl = amount_cents / 100
        message = (
            f"⚠️ Olá {name}, sua parcela de *R$ {amount_brl:.2f}* está em atraso há *{days_past_due} dia(s)*.\n"
            f"Regularize agora para evitar restrições no seu limite. Acesse o app Pagaê."
        )
        return self.send_text(phone, message)

    def send_checkout_approved(self, phone: str, name: str, merchant_name: str, total_cents: int) -> dict[str, Any]:
        total_brl = total_cents / 100
        message = (
            f"✅ Compra aprovada! Olá {name}, sua compra de *R$ {total_brl:.2f}* em *{merchant_name}* "
            f"foi aprovada pelo Pagaê. Pague a 1ª parcela via Pix para concluir."
        )
        return self.send_text(phone, message)
