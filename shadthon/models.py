from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class User:
    guid: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    raw: dict[str, Any] | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "User":

        return cls(
            guid=data.get(
                "user_guid",
                data.get("guid"),
            ),
            username=data.get(
                "username"
            ),
            first_name=data.get(
                "first_name"
            ),
            last_name=data.get(
                "last_name"
            ),
            phone=data.get(
                "phone"
            ),
            raw=data,
        )


@dataclass
class Message:
    message_id: int | str | None = None
    object_guid: str | None = None
    text: str | None = None
    sender_guid: str | None = None
    raw: dict[str, Any] | None = None

    @property
    def id(self):
        return self.message_id

    @property
    def chat_id(self):
        return self.object_guid

    @property
    def author_guid(self):
        return self.sender_guid

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        if not self.raw:
            return default

        return self.raw.get(
            key,
            default,
        )


@dataclass
class Poll:
    poll_id: str | int | None = None
    question: str | None = None
    options: list[Any] | None = None
    raw: dict[str, Any] | None = None


@dataclass
class LoginResult:
    user: User | None = None
    auth: str | None = None
    raw: dict[str, Any] | None = None