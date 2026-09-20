from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Session:
    phone_number: str | None = None
    auth: str | None = None
    decoded_auth: dict | None = None

    temporary_session: str | None = None

    key_hex: str | None = None
    iv_hex: str | None = None

    messenger_host: str | None = None

    user_guid: str | None = None

    state: str = "new"

    private_key_pem: str | None = None

    def save(
        self,
        path: str | Path,
    ) -> None:
        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                asdict(self),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(
        cls,
        path: str | Path,
    ) -> "Session":
        path = Path(path)

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        return cls(**data)


class SessionStore:

    def __init__(
        self,
        directory: str = "sessions",
    ):
        self.directory = Path(directory)

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def path_for(
        self,
        phone: str,
    ) -> Path:
        safe = (
            phone
            .replace("+", "")
            .replace(" ", "")
            .replace("-", "")
        )

        return self.directory / f"{safe}.json"

    def save(
        self,
        session: Session,
    ) -> None:
        if not session.phone_number:
            raise ValueError(
                "Session phone number is missing"
            )

        session.save(
            self.path_for(
                session.phone_number
            )
        )

    def load(
        self,
        phone: str,
    ) -> Session | None:
        path = self.path_for(phone)

        if not path.exists():
            return None

        return Session.load(path)

    def delete(
        self,
        phone: str,
    ) -> None:
        path = self.path_for(phone)

        if path.exists():
            path.unlink()