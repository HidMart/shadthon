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
        self.transport.private_key = (
            self.private_key
        )

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

        return await self.transport.request(
            "registerDevice",
            data,
            authenticated=True,
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

        if reply_to_message_id is not None:
            data["reply_to_message_id"] = (
                reply_to_message_id
            )

        return await self.transport.request(
            "sendMessage",
            data,
            authenticated=True,
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

        data = {
            "object_guid": object_guid,
            "limit": limit,
            "sort": "FromMax",
        }

        if max_id is not None:
            data["max_id"] = max_id

        if min_id is not None:
            data["min_id"] = min_id

        return await self.transport.request(
            "getMessages",
            data,
            authenticated=True,
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
            data["start_id"] = start_id

        return await self.transport.request(
            "getChats",
            data,
            authenticated=True,
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

        return await self.transport.request(
            "getChatsUpdates",
            {
                "state": str(state),
            },
            authenticated=True,
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

        return await self.transport.request(
            "getMessagesUpdates",
            {
                "object_guid": object_guid,
                "state": str(state),
            },
            authenticated=True,
            client_info=self._client_info(),
        )

    def on_message(
        self,
        handler=None,
    ):
        if handler is None:

            def decorator(func):
                self._message_handlers.append(func)
                return func

            return decorator

        self._message_handlers.append(handler)

        return handler

    def on_event(
        self,
        handler=None,
    ):
        if handler is None:

            def decorator(func):
                self._event_handlers.append(func)
                return func

            return decorator

        self._event_handlers.append(handler)

        return handler

    async def _handle_event(
        self,
        event,
    ):
        for handler in self._event_handlers:
            try:
                result = handler(event)

                if asyncio.iscoroutine(result):
                    await result

            except Exception as exc:
                print(
                    "Event handler error:",
                    exc,
                )

        messages = self._extract_messages(
            event
        )

        for item in messages:
            message = self._message_from_item(
                item
            )

            if message is None:
                continue

            for handler in self._message_handlers:
                try:
                    result = handler(message)

                    if asyncio.iscoroutine(result):
                        await result

                except Exception as exc:
                    print(
                        "Message handler error:",
                        exc,
                    )

    def _extract_messages(
        self,
        event,
    ):
        if not isinstance(event, dict):
            return []

        result = []

        data = event.get("data")

        if isinstance(data, dict):
            messages = data.get("messages")

            if isinstance(messages, list):
                result.extend(
                    item
                    for item in messages
                    if isinstance(item, dict)
                )

            message = data.get("message")

            if isinstance(message, dict):
                result.append(message)

            result.append(data)

        messages = event.get("messages")

        if isinstance(messages, list):
            result.extend(
                item
                for item in messages
                if isinstance(item, dict)
            )

        message = event.get("message")

        if isinstance(message, dict):
            result.append(message)

        result.append(event)

        unique = []
        seen = set()

        for item in result:
            if not isinstance(item, dict):
                continue

            marker = id(item)

            if marker in seen:
                continue

            seen.add(marker)
            unique.append(item)

        return unique

    def _message_from_item(
        self,
        item,
    ):
        if not isinstance(item, dict):
            return None

        message = item.get("message")

        if isinstance(message, dict):
            item = message

        text = (
            item.get("text")
            or item.get("message")
            or item.get("body")
        )

        if text is None:
            return None

        object_guid = (
            item.get("object_guid")
            or item.get("objectGuid")
            or item.get("chat_guid")
            or item.get("chatGuid")
        )

        author_guid = (
            item.get("author_guid")
            or item.get("authorGuid")
            or item.get("sender_guid")
            or item.get("senderGuid")
        )

        message_id = (
            item.get("message_id")
            or item.get("messageId")
            or item.get("id")
        )

        return Message(
            client=self,
            message_id=message_id,
            text=text,
            object_guid=object_guid,
            author_guid=author_guid,
            chat_id=object_guid,
            raw=item,
        )

    async def _poll_chat_updates(
        self,
        interval=1.0,
    ):
        state = self._chat_states.get(
            "state",
            0,
        )

        while self._running:
            try:
                result = await self.get_chats_updates(
                    state
                )

                await self._handle_event(
                    result
                )

                data = (
                    result.get("data")
                    if isinstance(result, dict)
                    else None
                )

                if isinstance(data, dict):
                    new_state = data.get(
                        "state"
                    )

                    if new_state is not None:
                        try:
                            state = int(
                                new_state
                            )
                        except (
                            TypeError,
                            ValueError,
                        ):
                            state = new_state

                        self._chat_states[
                            "state"
                        ] = state

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                print(
                    "Chat update error:",
                    exc,
                )

            await asyncio.sleep(interval)

    async def start(
        self,
        interval=1.0,
    ):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated"
            )

        self._running = True

        await self._poll_chat_updates(
            interval=interval
        )

    async def run_async(
        self,
        interval=1.0,
    ):
        await self.start(
            interval=interval
        )

    def run(
        self,
        interval=1.0,
    ):
        asyncio.run(
            self.start(
                interval=interval
            )
        )

    async def close(self):
        self._running = False

        close_method = getattr(
            self.transport,
            "close",
            None,
        )

        if close_method:
            result = close_method()

            if asyncio.iscoroutine(result):
                await result

    @staticmethod
    def _client_info():
        return {
            "app_name": "Main",
            "app_version": "4.4.26",
            "platform": "Web",
            "package": "web.shad.ir",
            "lang_code": "fa",
        }