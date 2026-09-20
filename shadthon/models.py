from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    raw: dict

    @property
    def message_id(self):
        return self.raw.get("message_id")

    @property
    def object_guid(self):
        return self.raw.get("object_guid")

    @property
    def text(self):
        message = self.raw.get(
            "message",
            {}
        )

        if isinstance(message, dict):
            return message.get(
                "text"
            )

        return self.raw.get("text")

    @property
    def sender_guid(self):
        return self.raw.get(
            "author_object_guid"
        )

    def get(self, key: str, default=None):
        return self.raw.get(
            key,
            default
        )


@dataclass
class User:
    raw: dict

    @property
    def user_guid(self):
        return self.raw.get(
            "user_guid"
        )

    @property
    def first_name(self):
        return self.raw.get(
            "first_name"
        )

    @property
    def last_name(self):
        return self.raw.get(
            "last_name"
        )


@dataclass
class LoginResult:
    auth: str
    user_guid: str | None = None