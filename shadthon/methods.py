from __future__ import annotations

import os
import random


class Methods:
    def __init__(self, transport):
        self.transport = transport

    async def send_message(
        self,
        object_guid,
        text,
        reply_to_message_id=None,
    ):
        data = {
            "object_guid": str(object_guid),
            "rnd": str(
                int.from_bytes(
                    os.urandom(8),
                    "big",
                )
            ),
            "text": str(text),
        }

        if reply_to_message_id is not None:
            data["reply_to_message_id"] = str(
                reply_to_message_id
            )

        return await self.transport.send_authenticated(
            "sendMessage",
            data,
        )

    async def edit_message(
        self,
        object_guid,
        message_id,
        text,
    ):
        return await self.transport.send_authenticated(
            "editMessage",
            {
                "object_guid": str(object_guid),
                "message_id": str(message_id),
                "text": str(text),
            },
        )

    async def delete_message(
        self,
        object_guid,
        message_id,
    ):
        return await self.transport.send_authenticated(
            "deleteMessage",
            {
                "object_guid": str(object_guid),
                "message_id": str(message_id),
            },
        )

    async def delete_messages(
        self,
        object_guid,
        message_ids,
    ):
        return await self.transport.send_authenticated(
            "deleteMessages",
            {
                "object_guid": str(object_guid),
                "message_ids": [
                    str(x)
                    for x in message_ids
                ],
            },
        )

    async def get_messages(
        self,
        object_guid,
        limit=50,
        sort="FromMax",
        max_id=None,
        min_id=None,
    ):
        data = {
            "object_guid": str(object_guid),
            "limit": int(limit),
            "sort": str(sort),
        }

        if max_id is not None:
            data["max_id"] = str(max_id)

        if min_id is not None:
            data["min_id"] = str(min_id)

        return await self.transport.send_authenticated(
            "getMessages",
            data,
        )

    async def get_chats(self, start_id=None):
        data = {}

        if start_id is not None:
            data["start_id"] = str(start_id)

        return await self.transport.send_authenticated(
            "getChats",
            data,
        )

    async def get_chats_updates(self, state=0):
        return await self.transport.send_authenticated(
            "getChatsUpdates",
            {
                "state": str(state),
            },
        )

    async def get_messages_updates(
        self,
        object_guid,
        state=0,
    ):
        return await self.transport.send_authenticated(
            "getMessagesUpdates",
            {
                "object_guid": str(object_guid),
                "state": str(state),
            },
        )

    async def register_device(self):
        return await self.transport.send_authenticated(
            "registerDevice",
            {
                "app_version": "WB_4.4.26",
                "device_hash": "".join(
                    random.choices(
                        "0123456789",
                        k=26,
                    )
                ),
                "device_model": "Chrome 153",
                "is_multi_account": False,
                "lang_code": "fa",
                "system_version": "Mac/iOS",
                "token": "",
                "token_type": "Web",
            },
        )

    async def invoke(self, method, **kwargs):
        return await self.transport.send_authenticated(
            method,
            kwargs,
        )