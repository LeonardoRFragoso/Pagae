"""Privacy helpers for masking sensitive data in logs and responses."""


def mask_cpf(value: str | None) -> str:
    if not value:
        return ""
    digits = "".join(c for c in value if c.isdigit())
    if len(digits) != 11:
        return "***"
    return f"{digits[:3]}.***.***-{digits[-2:]}"


def mask_cnpj(value: str | None) -> str:
    if not value:
        return ""
    digits = "".join(c for c in value if c.isdigit())
    if len(digits) != 14:
        return "***"
    return f"{digits[:2]}.***.***/{digits[8:12]}-{digits[-2:]}"


def mask_email(value: str | None) -> str:
    if not value:
        return ""
    if "@" not in value:
        return "***"
    local, domain = value.split("@", 1)
    masked_local = (
        "*" * len(local)
        if len(local) <= 2
        else f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}"
    )
    return f"{masked_local}@{domain}"


def mask_phone(value: str | None) -> str:
    if not value:
        return ""
    digits = "".join(c for c in value if c.isdigit())
    if len(digits) < 8:
        return "***"
    return f"****-{digits[-4:]}"


def mask_api_key(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:8]}{'*' * (len(value) - 8)}"
