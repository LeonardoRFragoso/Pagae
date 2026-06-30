"""Brevo (formerly Sendinblue) email stub integration.

In production, replace _send with real HTTP calls to api.brevo.com/v3/smtp/email.
Free tier: 300 emails/day.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class BrevoClient:
    def __init__(self, api_key: str = "stub") -> None:
        self.api_key = api_key

    def send_transactional(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
    ) -> dict[str, Any]:
        logger.info(
            "brevo_send_email",
            extra={"to": to_email, "subject": subject},
        )
        return {"messageId": f"<stub-{to_email}>", "status": "sent"}

    def send_payment_reminder(self, to_email: str, to_name: str, amount_cents: int, due_date: str) -> dict[str, Any]:
        amount_brl = amount_cents / 100
        html = (
            f"<p>Olá <strong>{to_name}</strong>,</p>"
            f"<p>Você tem uma parcela de <strong>R$ {amount_brl:.2f}</strong> "
            f"vencendo em <strong>{due_date}</strong>.</p>"
            f"<p>Acesse o app Pagaê para visualizar o QR Code e realizar o pagamento.</p>"
        )
        return self.send_transactional(to_email, to_name, "Lembrete de parcela — Pagaê", html)

    def send_overdue_reminder(
        self, to_email: str, to_name: str, amount_cents: int, days_past_due: int
    ) -> dict[str, Any]:
        amount_brl = amount_cents / 100
        html = (
            f"<p>Olá <strong>{to_name}</strong>,</p>"
            f"<p>Sua parcela de <strong>R$ {amount_brl:.2f}</strong> está em atraso há "
            f"<strong>{days_past_due} dia(s)</strong>.</p>"
            f"<p>Regularize agora para manter seu limite disponível no Pagaê.</p>"
        )
        return self.send_transactional(to_email, to_name, "Parcela em atraso — Pagaê", html)

    def send_checkout_approved(
        self, to_email: str, to_name: str, merchant_name: str, total_cents: int
    ) -> dict[str, Any]:
        total_brl = total_cents / 100
        html = (
            f"<p>Olá <strong>{to_name}</strong>,</p>"
            f"<p>Sua compra de <strong>R$ {total_brl:.2f}</strong> em <strong>{merchant_name}</strong> "
            f"foi aprovada pelo Pagaê! 🎉</p>"
            f"<p>Pague a 1ª parcela via Pix para concluir a compra.</p>"
        )
        return self.send_transactional(to_email, to_name, "Compra aprovada — Pagaê", html)
