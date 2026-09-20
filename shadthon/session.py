from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Session:
    phone_number: str | None = None
    auth: str | None = None
    user_guid: str | None = None
    messenger_host: str | None = None
    state: str = "new"

    private_key_pem: str | None = None
    public_key_pem: str | None = None

    temporary_session: str | None = None
    phone_code_hash: str | None = None

    key_hex: str | None = None
    iv_hex: str | None = None

    decoded_auth: dict[str, Any] | None = None

    def set_key(self, key: bytes) -> None:
        self.key_hex = key.hex()

    def set_iv(self, iv: bytes) -> None:
        self.iv_hex = iv.hex()

    def get_key(self) -> bytes | None:
        if not self.key_hex:
            return None

        try:
            return bytes.fromhex(self.key_hex)
        except ValueError:
            return None

    def get_iv(self) -> bytes:
        if not self.iv_hex:
            return b"\x00" * 16

        try:
            return bytes.fromhex(self.iv_hex)
        except ValueError:
            return b"\x00" * 16

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        target.write_text(
            json.dumps(
                asdict(self),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "Session":
        target = Path(path)

        if not target.exists():
            return cls()

        try:
            data = json.loads(
                target.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            return cls()

        if not isinstance(data, dict):
            return cls()

        allowed = {
            "phone_number",
            "auth",
            "user_guid",
            "messenger_host",
            "state",
            "private_key_pem",
            "public_key_pem",
            "temporary_session",
            "phone_code_hash",
            "key_hex",
            "iv_hex",
            "decoded_auth",
        }

        clean = {
            key: value
            for key, value in data.items()
            if key in allowed
        }

        return cls(**clean)

    def clear(self, path: str | Path) -> None:
        target = Path(path)

        if target.exists():
            target.unlink()

        self.phone_number = None
        self.auth = None
        self.user_guid = None
        self.messenger_host = None
        self.state = "new"

        self.private_key_pem = None
        self.public_key_pem = None

        self.temporary_session = None
        self.phone_code_hash = None

        self.key_hex = None
        self.iv_hex = None
        self.decoded_auth = None