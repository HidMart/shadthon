from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Session:
    def __init__(
        self,
        phone_number: str | None = None,
        auth: str | None = None,
        user_guid: str | None = None,
        messenger_host: str | None = None,
        api_hosts: list[str] | None = None,
        websocket_hosts: list[str] | None = None,
        state: str = "unauthenticated",
    ):
        self.phone_number = phone_number
        self.auth = auth
        self.user_guid = user_guid
        self.messenger_host = messenger_host

        self.api_hosts = api_hosts or []
        self.websocket_hosts = websocket_hosts or []

        self.state = state

    @classmethod
    def load(
        cls,
        path: Path,
    ) -> "Session":

        if not path.exists():
            return cls()

        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            return cls()

        if not isinstance(data, dict):
            return cls()

        return cls(
            phone_number=data.get(
                "phone_number"
            ),
            auth=data.get(
                "auth"
            ),
            user_guid=data.get(
                "user_guid"
            ),
            messenger_host=data.get(
                "messenger_host"
            ),
            api_hosts=data.get(
                "api_hosts",
                [],
            ),
            websocket_hosts=data.get(
                "websocket_hosts",
                [],
            ),
            state=data.get(
                "state",
                "unauthenticated",
            ),
        )

    def save(
        self,
        path: Path,
    ) -> None:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "phone_number":
                self.phone_number,
            "auth":
                self.auth,
            "user_guid":
                self.user_guid,
            "messenger_host":
                self.messenger_host,
            "api_hosts":
                self.api_hosts,
            "websocket_hosts":
                self.websocket_hosts,
            "state":
                self.state,
        }

        path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def clear(
        self,
        path: Path,
    ) -> None:

        self.phone_number = None
        self.auth = None
        self.user_guid = None
        self.messenger_host = None
        self.api_hosts = []
        self.websocket_hosts = []
        self.state = "unauthenticated"

        if path.exists():
            path.unlink()

    def get_key(self) -> bytes | None:
        if not self.auth:
            return None

        from .crypto import Crypto

        return Crypto(
            self.auth
        ).key

    def get_iv(self) -> bytes | None:
        if not self.auth:
            return None

        from .crypto import Crypto

        return Crypto(
            self.auth
        ).iv

    def set_auth(
        self,
        auth: str,
    ) -> None:

        self.auth = auth
        self.state = "authenticated"