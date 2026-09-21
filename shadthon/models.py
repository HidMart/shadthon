from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class User:
    guid: str
    name: str = ""
    username: str = ""
    bio: str = ""
    phone: str = ""
    is_verified: bool = False

    @classmethod
    def from_dict(cls, data):
        profile = (
            data.get("user", data)
            if isinstance(data, dict)
            else {}
        )

        if not isinstance(profile, dict):
            profile = {}

        first = profile.get(
            "first_name",
            "",
        )

        last = profile.get(
            "last_name",
            "",
        )

        return cls(
            guid=profile.get(
                "user_guid",
                "",
            ),
            name=f"{first} {last}".strip(),
            username=profile.get(
                "username",
                "",
            ),
            bio=profile.get(
                "bio",
                "",
            ),
            phone=profile.get(
                "phone",
                "",
            ),
            is_verified=bool(
                profile.get(
                    "is_verified",
                    False,
                )
            ),
        )


@dataclass
class Chat:
    guid: str
    title: str = ""
    type: str = "User"
    username: Optional[str] = None
    description: Optional[str] = None
    members_count: int = 0
    raw: Dict[str, Any] = field(
        default_factory=dict
    )
    _client: Any = field(
        default=None,
        repr=False,
        compare=False,
    )

    @classmethod
    def from_dict(
        cls,
        data,
        client=None,
    ):
        raw = data or {}

        group = raw.get("group")
        channel = raw.get("channel")
        user = raw.get("user")

        if isinstance(group, dict):
            return cls(
                guid=group.get(
                    "group_guid"
                )
                or raw.get(
                    "object_guid",
                    "",
                ),
                title=group.get(
                    "group_title"
                )
                or group.get(
                    "title",
                    "",
                ),
                type="Group",
                username=group.get(
                    "username"
                ),
                description=group.get(
                    "description"
                ),
                members_count=int(
                    group.get(
                        "count_members",
                        0,
                    )
                    or 0
                ),
                raw=raw,
                _client=client,
            )

        if isinstance(channel, dict):
            return cls(
                guid=channel.get(
                    "channel_guid"
                )
                or raw.get(
                    "object_guid",
                    "",
                ),
                title=channel.get(
                    "channel_title"
                )
                or channel.get(
                    "title",
                    "",
                ),
                type="Channel",
                username=channel.get(
                    "username"
                ),
                description=channel.get(
                    "description"
                ),
                members_count=int(
                    channel.get(
                        "count_members",
                        0,
                    )
                    or 0
                ),
                raw=raw,
                _client=client,
            )

        if isinstance(user, dict):
            first = user.get(
                "first_name",
                "",
            )
            last = user.get(
                "last_name",
                "",
            )

            return cls(
                guid=user.get(
                    "user_guid"
                )
                or raw.get(
                    "object_guid",
                    "",
                ),
                title=f"{first} {last}".strip(),
                type="User",
                username=user.get(
                    "username"
                ),
                description=user.get(
                    "bio"
                ),
                raw=raw,
                _client=client,
            )

        guid = (
            raw.get("object_guid")
            or raw.get("guid")
            or ""
        )

        if guid.startswith("g0"):
            chat_type = "Group"
        elif guid.startswith("c0"):
            chat_type = "Channel"
        elif guid.startswith("b0"):
            chat_type = "Bot"
        elif guid.startswith("s0"):
            chat_type = "Service"
        else:
            chat_type = "User"

        return cls(
            guid=guid,
            title=raw.get(
                "title"
            )
            or raw.get(
                "first_name",
                "",
            ),
            type=chat_type,
            username=raw.get(
                "username"
            ),
            description=raw.get(
                "description"
            )
            or raw.get(
                "bio"
            ),
            members_count=int(
                raw.get(
                    "count_members",
                    0,
                )
                or 0
            ),
            raw=raw,
            _client=client,
        )


@dataclass
class Message:
    id: str
    text: str
    author_guid: str
    chat_guid: str
    message_type: str = "Text"
    reply_to_message_id: Optional[str] = None
    is_edited: bool = False
    raw: Dict[str, Any] = field(
        default_factory=dict
    )
    _client: Any = field(
        default=None,
        repr=False,
        compare=False,
    )

    @classmethod
    def from_dict(
        cls,
        data,
        client=None,
    ):
        if not isinstance(data, dict):
            data = {}

        nested = data.get(
            "message"
        )

        if not isinstance(
            nested,
            dict,
        ):
            nested = {}

        return cls(
            id=str(
                data.get(
                    "message_id"
                )
                or nested.get(
                    "message_id"
                )
                or ""
            ),
            text=(
                data.get("text")
                or nested.get("text")
                or ""
            ),
            author_guid=(
                data.get(
                    "author_object_guid"
                )
                or nested.get(
                    "author_object_guid"
                )
                or ""
            ),
            chat_guid=(
                data.get(
                    "object_guid"
                )
                or nested.get(
                    "object_guid"
                )
                or ""
            ),
            message_type=(
                data.get("type")
                or nested.get("type")
                or "Text"
            ),
            reply_to_message_id=(
                data.get(
                    "reply_to_message_id"
                )
                or nested.get(
                    "reply_to_message_id"
                )
            ),
            is_edited=bool(
                data.get(
                    "is_edited"
                )
                or nested.get(
                    "is_edited"
                )
                or False
            ),
            raw=data,
            _client=client,
        )

    async def reply(self, text):
        if self._client is None:
            raise RuntimeError(
                "Message is not bound to Client."
            )

        return await self._client.send_message(
            self.chat_guid,
            text=text,
            reply_to_message_id=self.id,
        )

    async def answer(self, text):
        return await self.reply(text)

    def get(self, key, default=None):
        return self.raw.get(
            key,
            default,
        )

    def __getitem__(self, key):
        return self.raw[key]