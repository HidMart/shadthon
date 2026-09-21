from __future__ import annotations

import os
import time
import uuid


class Methods:
    def __init__(self, session, transport, client=None):
        self.session = session
        self.transport = transport
        self.client = client

    async def send_code(self, phone):
        return await self.transport.send_handshake(
            "sendCode",
            {
                "phone_number": phone,
                "send_type": "SMS",
            },
        )

    async def sign_in(self, phone, phone_code, phone_code_hash):
        return await self.transport.send_handshake(
            "signIn",
            {
                "phone_number": phone,
                "phone_code_hash": phone_code_hash,
                "phone_code": phone_code,
                "public_key": self.session.data.get("public_key", ""),
            },
        )

    async def register_device(self):
        device_hash = "".join(
            __import__("random").choices(
                "0123456789",
                k=26,
            )
        )

        data = {
            "app_version": "WB_4.4.26",
            "device_hash": device_hash,
            "device_model": "Chrome 153",
            "is_multi_account": False,
            "lang_code": "fa",
            "system_version": "Mac/iOS",
            "token": "",
            "token_type": "Web",
        }

        return await self.transport.send_authenticated(
            "registerDevice",
            data,
        )

    async def send_message(
        self,
        object_guid,
        text="",
        reply_to_message_id=None,
        file_inline=None,
    ):
        data = {
            "object_guid": object_guid,
            "rnd": str(
                int.from_bytes(
                    os.urandom(4),
                    "big",
                )
            ),
            "text": text,
        }

        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id

        if file_inline:
            data["file_inline"] = file_inline

        return await self.transport.send_authenticated(
            "sendMessage",
            data,
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
            "object_guid": object_guid,
            "limit": limit,
            "sort": sort,
        }

        if max_id is not None:
            data["max_id"] = max_id

        if min_id is not None:
            data["min_id"] = min_id

        return await self.transport.send_authenticated(
            "getMessages",
            data,
        )

    async def get_chats_updates(self, state=None):
        if not state or state <= 0:
            state = self.session.state or int(time.time()) - 150

        return await self.transport.send_authenticated(
            "getChatsUpdates",
            {
                "state": str(state),
            },
        )

    async def get_messages_updates(
        self,
        object_guid,
        state=None,
    ):
        if not state or state <= 0:
            state = int(time.time()) - 150

        return await self.transport.send_authenticated(
            "getMessagesUpdates",
            {
                "object_guid": object_guid,
                "state": str(state),
            },
        )

    async def get_chats(self, start_id=None):
        data = {}

        if start_id:
            data["start_id"] = start_id

        return await self.transport.send_authenticated(
            "getChats",
            data,
        )