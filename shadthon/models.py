from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class User:
    guid: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    phone_number: str | None = None

    raw: dict[str, Any] = field(
        default_factory=dict
    )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "User":

        return cls(
            guid=(
                data.get("guid")
                or data.get("user_guid")
            ),
            first_name=data.get(
                "first_name"
            ),
            last_name=data.get(
                "last_name"
            ),
            username=data.get(
                "username"
            ),
            phone_number=data.get(
                "phone_number"
            ),
            raw=dict(data),
        )


@dataclass
class Message:
    message_id: int | str | None = None
    object_guid: str | None = None
    text: str | None = None
    sender_guid: str | None = None

    raw: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class Poll:
    poll_id: str | int | None = None
    question: str | None = None
    options: list[Any] = field(
        default_factory=list
    )

    raw: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class FileInfo:
    file_id: str | int | None = None
    dc_id: str | int | None = None
    access_hash: str | None = None
    file_name: str | None = None
    size: int | None = None
    mime: str | None = None
    file_type: str | None = None

    raw: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class LoginResult:
    user: User | None = None
    auth: str | None = None

    raw: dict[str, Any] = field(
        default_factory=dict
    )