from __future__ import annotations

import json
import random
import re
import secrets


def generate_session_id() -> str:
    return secrets.token_hex(16)


def random_id() -> str:
    return str(
        random.randint(
            100000,
            999999999,
        )
    )


def normalize_phone(
    phone: str | None,
) -> str:
    if not phone:
        raise ValueError(
            "Phone number is required."
        )

    phone = re.sub(
        r"[^\d+]",
        "",
        phone.strip(),
    )

    if phone.startswith("+"):
        phone = phone[1:]

    if phone.startswith("0098"):
        phone = phone[2:]

    if phone.startswith("98"):
        return phone

    if phone.startswith("0"):
        return "98" + phone[1:]

    return phone


def json_text(
    value: object,
) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    )