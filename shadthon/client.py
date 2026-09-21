from __future__ import annotations

import asyncio
import os
import random

from .auth import AuthManager
from .models import Message
from .session import Session
from .transport import Transport


class Client:
    def __init__(
        self,
        session_name="default",
        phone=None,
        base_url="https://shadmessenger36.iranlms.ir",
        socket_url=None,
        auth=None,
        session=None,
    ):
        self.session = (
            session
            if isinstance(session, Session)
            else Session(session_name)
        )

        if phone:
            self.session.data["phone"] = phone

        self.base_url = base_url
        self.socket_url = socket_url

        self.auth = auth or self.session.auth
        self.private_key = self.session.private_key

        self.transport = Transport(
            base_url=self.base_url,
            auth=self.auth,
            private_key=self.private_key,
        )

        self.auth_manager = AuthManager(
            self.transport,
            self.session,
        )

        self._message_handlers = []
        self._event_handlers = []

        self._running = False
        self._chat_states = {}
        self._message_states = {}

    @property
    def authenticated(self):
        return bool(self.session.auth)

    def _client_info(self):
        return {
            "app_name": "Main",
            "app_version": "4.4.26",
            "platform": "Web",
            "package": "web.shad.ir",
            "lang_code": "fa",
        }

    async def send_code(self, phone=None):
        phone = phone or self.session.phone

        if not phone:
            raise ValueError(
                "Phone number is required"
            )

        return await self.auth_manager.send_code(
            phone
        )

    async def sign_in(
        self,
        phone=None,
        phone_code=None,
        phone_code_hash=None,
    ):
        phone = phone or self.session.phone

        if not phone:
            raise ValueError(
                "Phone number is required"
            )

        if not phone_code:
            raise ValueError(
                "Login code is required"
            )

        result = await self.auth_manager.sign_in(
            phone=phone,
            phone_code=phone_code,
            phone_code_hash=phone_code_hash,
        )

        self.auth = self.session.auth
        self.private_key = self.session.private_key

        self.transport.auth = self.auth
        self.transport.private_key = self.private_key

        return result

    async def register_device(self):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated"
            )

        device_hash = "".join(
            random.choices(
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
            client_info=self._client_info(),
        )

    async def send_message(
        self,
        object_guid,
        text,
        reply_to_message_id=None,
    ):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated"
            )

        if not object_guid:
            raise ValueError(
                "object_guid is required"
            )

        if not text:
            raise ValueError(
                "text is required"
            )

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
            client_info=self._client_info(),
        )

    async def get_messages(
        self,
        object_guid,
        limit=20,
        max_id=None,
        min_id=None,
    ):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated"
            )

        if not object_guid:
            raise ValueError(
                "object_guid is required"
            )

        data = {
            "object_guid": str(object_guid),
            "limit": int(limit),
            "sort": "FromMax",
        }

        if max_id is not None:
            data["max_id"] = str(max_id)

        if min_id is not None:
            data["min_id"] = str(min_id)

        return await self.transport.send_authenticated(
            "getMessages",
            data,
            client_info=self._client_info(),
        )

    async def get_chats(
        self,
        start_id=None,
    ):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated"
            )

        data = {}

        if start_id is not None:
            data["start_id"] = str(start_id)

        return await self.transport.send_authenticated(
            "getChats",
            data,
            client_info=self._client_info(),
        )

    async def get_chats_updates(
        self,
        state=0,
    ):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated"
            )

        data = {
            "state": str(state),
        }

        return await self.transport.send_authenticated(
            "getChatsUpdates",
            data,
            client_info=self._client_info(),
        )

    async def get_messages_updates(
        self,
        object_guid,
        state=0,
    ):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated"
            )

        if not object_guid:
            raise ValueError(
                "object_guid is required"
            )

        data = {
            "object_guid": str(object_guid),
            "state": str(state),
        }

        return await self.transport.send_authenticated(
            "getMessagesUpdates",
            data,
            client_info=self._client_info(),
        )

    def on_message(self, handler=None):
        if handler is None:
            def decorator(func):
                self._message_handlers.append(func)
                return func

            return decorator

        self._message_handlers.append(handler)

        return handler

    def on_event(self, handler=None):
        if handler is None:
            def decorator(func):
                self._event_handlers.append(func)
                return func

            return decorator

        self._event_handlers.append(handler)

        return handler

    async def _call_handler(
        self,
        handler,
        message,
    ):
        result = handler(message)

        if asyncio.iscoroutine(result):
            await result

    async def _handle_message(
        self,
        message,
    ):
        for handler in list(
            self._message_handlers
        ):
            try:
                await self._call_handler(
                    handler,
                    message,
                )
            except Exception:
                continue

    async def _handle_event(
        self,
        event,
    ):
        for handler in list(
            self._event_handlers
        ):
            try:
                result = handler(event)

                if asyncio.iscoroutine(result):
                    await result

            except Exception:
                continue

    def _extract_messages(
        self,
        result,
    ):
        messages = []

        if not isinstance(result, dict):
            return messages

        def walk(value):
            if isinstance(value, dict):
                if (
                    "message_id" in value
                    or "messageId" in value
                ):
                    messages.append(value)

                for item in value.values():
                    walk(item)

            elif isinstance(value, list):
                for item in value:
                    walk(item)

        walk(result)

        return messages

    def _message_from_dict(
        self,
        data,
    ):
        if not isinstance(data, dict):
            return None

        try:
            if hasattr(
                Message,
                "from_dict",
            ):
                return Message.from_dict(data)
        except Exception:
            pass

        try:
            return Message(**data)
        except Exception:
            return data

    async def _poll_messages(
        self,
        interval=2,
    ):
        while self._running:
            try:
                result = await self.get_chats_updates(
                    state=0
                )

                await self._handle_event(result)

                raw_messages = self._extract_messages(
                    result
                )

                for raw in raw_messages:
                    message = self._message_from_dict(
                        raw
                    )

                    if message is not None:
                        await self._handle_message(
                            message
                        )

            except asyncio.CancelledError:
                raise

            except Exception:
                pass

            await asyncio.sleep(interval)

    async def start(
        self,
        interval=2,
    ):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated"
            )

        self._running = True

        await self._poll_messages(
            interval=interval
        )

    async def run_async(
        self,
        interval=2,
    ):
        await self.start(
            interval=interval
        )

    def run(
        self,
        interval=2,
    ):
        try:
            asyncio.run(
                self.start(
                    interval=interval
                )
            )
        except KeyboardInterrupt:
            self._running = False

    async def stop(self):
        self._running = False

    async def close(self):
        self._running = False

        try:
            await self.transport.close()
        except Exception:
            pass