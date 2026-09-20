from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class User:
    guid: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    phone_number: str | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "User":
        return cls(
            guid=data.get("user_guid")
            or data.get("guid"),

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
        )


@dataclass(slots=True)
class Message:
    message_id: str | None = None
    object_guid: str | None = None
    text: str | None = None
    sender_guid: str | None = None
    raw: dict[str, Any] | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Message":
        return cls(
            message_id=str(
                data.get("message_id")
                or data.get("id")
                or ""
            ),

            object_guid=data.get(
                "object_guid"
            ),

            text=data.get(
                "text"
            ),

            sender_guid=(
                data.get("author_object_guid")
                or data.get("sender_guid")
                or data.get("user_guid")
            ),

            raw=data,
        )


@dataclass(slots=True)
class Poll:
    poll_id: str | None = None
    question: str | None = None
    options: list[Any] | None = None
    raw: dict[str, Any] | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Poll":
        return cls(
            poll_id=str(
                data.get("poll_id")
                or data.get("id")
                or ""
            ),

            question=data.get(
                "question"
            ),

            options=data.get(
                "options",
                [],
            ),

            raw=data,
        )


@dataclass(slots=True)
class FileInfo:
    file_id: str | None = None
    dc_id: str | None = None
    access_hash: str | None = None
    file_name: str | None = None
    size: int = 0
    mime: str | None = None
    file_type: str = "File"
    raw: dict[str, Any] | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "FileInfo":
        return cls(
            file_id=str(
                data.get("file_id")
                or ""
            ),

            dc_id=str(
                data.get("dc_id")
                or ""
            ),

            access_hash=(
                data.get("access_hash_rec")
                or data.get("access_hash")
            ),

            file_name=data.get(
                "file_name"
            ),

            size=int(
                data.get("size")
                or 0
            ),

            mime=data.get(
                "mime"
            ),

            file_type=data.get(
                "type",
                "File",
            ),

            raw=data,
        )


@dataclass(slots=True)
class LoginResult:
    user: User | None
    auth: str
    raw: dict[str, Any]