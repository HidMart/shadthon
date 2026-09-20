from __future__ import annotations

from typing import Any

from .models import Message
from .utils import random_id


class MessageManager:

    def __init__(self, transport):
        self.transport = transport

    async def send_message(
        self,
        object_guid: str,
        text: str,
        reply_to: str | None = None,
    ) -> dict[str, Any]:

        data: dict[str, Any] = {
            "object_guid": object_guid,
            "rnd": random_id(),
            "text": text,
        }

        if reply_to:
            data["reply_to_message_id"] = reply_to

        return await self.transport.authenticated(
            "sendMessage",
            data,
        )

    async def get_messages(
        self,
        object_guid: str,
        middle_message_id: str = "0",
    ) -> list[Message]:

        result = await self.transport.authenticated(
            "getMessagesInterval",
            {
                "object_guid": object_guid,
                "middle_message_id":
                    middle_message_id,
            },
        )

        data = result.get(
            "data",
            result,
        )

        messages = data.get(
            "messages",
            [],
        )

        return [
            Message.from_dict(item)
            for item in messages
            if isinstance(item, dict)
        ]

    async def get_message(
        self,
        object_guid: str,
        message_id: str,
    ) -> Message | None:

        result = await self.transport.authenticated(
            "getMessagesByID",
            {
                "object_guid": object_guid,
                "message_ids": [
                    message_id
                ],
            },
        )

        data = result.get(
            "data",
            result,
        )

        messages = data.get(
            "messages",
            [],
        )

        if not messages:
            return None

        return Message.from_dict(
            messages[0]
        )