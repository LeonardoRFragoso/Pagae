"""DPD (Days Past Due) rule engine.

Buckets define what action to take based on how many days overdue an installment is.
Rules are evaluated in order; the first match wins.
"""

from dataclasses import dataclass


@dataclass
class DPDAction:
    send_whatsapp: bool = False
    send_email: bool = False
    generate_new_qr: bool = False
    suspend_limit: bool = False


# DPD → action mapping (threshold is inclusive lower bound)
DPD_RULES: list[tuple[int, DPDAction]] = [
    (1, DPDAction(send_whatsapp=True, send_email=False, generate_new_qr=True)),
    (3, DPDAction(send_whatsapp=True, send_email=True, generate_new_qr=True)),
    (7, DPDAction(send_whatsapp=True, send_email=True, generate_new_qr=True, suspend_limit=True)),
]


def get_action(days_past_due: int) -> DPDAction:
    """Return the DPD action for the given number of days past due."""
    action = DPDAction()
    for threshold, rule_action in reversed(DPD_RULES):
        if days_past_due >= threshold:
            return rule_action
    return action
