from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass
class Session:
    phone_number: str

    auth: str = ""
    decoded_auth: str = ""

    temporary_session: str = ""

    key_hex: str = ""
    iv_hex: str = ""

    messenger_host: str = ""

    user_guid: str = ""

    state: int = 0

    private_key_pem: str = ""

    def has_auth(self) -> bool:
        return bool(self.auth and self.key_hex)

    def set_key(self, value: bytes):
        self.key_hex = value.hex()

    def get_key(self) -> bytes:
        if not self.key_hex:
            return b""

        return bytes.fromhex(self.key_hex)

    def set_iv(self, value: bytes):
        self.iv_hex = value.hex()

    def get_iv(self) -> bytes:
        if self.iv_hex:
            return bytes.fromhex(self.iv_hex)

        return b"\x00" * 16

    def clear_auth(self):
        self.auth = ""
        self.decoded_auth = ""
        self.key_hex = ""
        self.iv_hex = ""
        self.user_guid = ""
        self.private_key_pem = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        allowed = {
            "phone_number",
            "auth",
            "decoded_auth",
            "temporary_session",
            "key_hex",
            "iv_hex",
            "messenger_host",
            "user_guid",
            "state",
            "private_key_pem",
        }

        clean = {
            key: value
            for key, value in data.items()
            if key in allowed
        }

        return cls(**clean)


class SessionStore:
    def __init__(self, directory="sessions"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, phone_number: str):
        safe = "".join(
            character
            for character in phone_number
            if character.isdigit()
        )

        return self.directory / f"{safe}.json"

    def save(self, session: Session):
        path = self._path(session.phone_number)

        path.write_text(
            json.dumps(
                session.to_dict(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(self, phone_number: str):
        path = self._path(phone_number)

        if not path.exists():
            return None

        try:
            data = json.loads(
                path.read_text(encoding="utf-8")
            )

            return Session.from_dict(data)

        except Exception:
            return None

    def delete(self, phone_number: str):
        path = self._path(phone_number)

        if path.exists():
            path.unlink()