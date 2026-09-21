from __future__ import annotations

import hashlib
import platform
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
                "public_key": self.session.data.get(
                    "public_key",
                    "",
                ),
            },
        )

    async def register_device(self):
        device_id = self.session.data.get("device_id")

        if not device_id:
            device_id = str(uuid.uuid4())
            self.session.data["device_id"] = device_id
            self.session.save()

        phone = self.session.phone or ""
        user_guid = self.session.user_guid or ""

        device_hash = hashlib.sha1(
            f"{phone}:{user_guid}:{device_id}".encode()
        ).hexdigest()

        data = {
            "app_version": "4.4.26",
            "device_hash": device_hash,
            "device_model": "Shadthon",
            "lang_code": "fa",
            "system_version": platform.system(),
            "token": " ",
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
            "rnd": str(uuid.uuid4()),
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

        if max_id:
            data["max_id"] = max_id

        if min_id:
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