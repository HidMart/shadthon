import asyncio

from .auth import AuthManager
from .models import Message
from .session import Session
from .transport import Transport
from .websocket import ShadWebSocket


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
            self.session.data[
                "phone"
            ] = phone

        self.base_url = base_url
        self.socket_url = socket_url

        self.auth = auth or self.session.auth
        self.private_key = (
            self.session.private_key
        )

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

        self.websocket = None

    @property
    def authenticated(self):
        return bool(
            self.session.auth
        )

    async def send_code(
        self,
        phone=None,
    ):
        phone = (
            phone
            or self.session.phone
        )

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
        phone = (
            phone
            or self.session.phone
        )

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
        self.private_key = (
            self.session.private_key
        )

        self.transport.auth = self.auth
        self.transport.private_key = (
            self.private_key
        )

        return result

    async def send_message(
        self,
        object_guid,
        text,
    ):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated"
            )

        return await self.transport.request(
            "sendMessage",
            {
                "object_guid": object_guid,
                "text": text,
            },
            authenticated=True,
        )

    async def get_messages(
        self,
        object_guid,
        limit=20,
    ):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated"
            )

        return await self.transport.request(
            "getMessages",
            {
                "object_guid": object_guid,
                "limit": limit,
            },
            authenticated=True,
        )

    def on_message(
        self,
        handler=None,
    ):
        if handler is None:
            def decorator(func):
                self._message_handlers.append(
                    func
                )
                return func

            return decorator

        self._message_handlers.append(
            handler
        )

        return handler

    def on_event(
        self,
        handler=None,
    ):
        if handler is None:
            def decorator(func):
                self._event_handlers.append(
                    func
                )
                return func

            return decorator

        self._event_handlers.append(
            handler
        )

        return handler

    async def _handle_event(
        self,
        event,
    ):
        for handler in self._event_handlers:
            try:
                await handler(event)
            except Exception as exc:
                print(
                    "Event handler error:",
                    exc,
                )

        message = self._message_from_event(
            event
        )

        if message is None:
            return

        for handler in self._message_handlers:
            try:
                await handler(message)
            except Exception as exc:
                print(
                    "Message handler error:",
                    exc,
                )

    def _message_from_event(
        self,
        event,
    ):
        if not isinstance(event, dict):
            return None

        candidates = []

        data = event.get("data")

        if isinstance(data, dict):
            candidates.append(data)

            nested = data.get("message")

            if isinstance(nested, dict):
                candidates.append(nested)

        candidates.append(event)

        for item in candidates:
            if not isinstance(item, dict):
                continue

            message = item.get("message")

            if isinstance(message, dict):
                item = message

            text = (
                item.get("text")
                or item.get("message")
            )

            if text is None:
                continue

            object_guid = (
                item.get("object_guid")
                or item.get("objectGuid")
            )

            author_guid = (
                item.get("author_guid")
                or item.get("authorGuid")
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

        return None

    async def start(self):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated"
            )

        if not self.socket_url:
            raise RuntimeError(
                "socket_url is required for receiving messages"
            )

        self.websocket = ShadWebSocket(
            url=self.socket_url,
            auth=self.auth,
            on_event=self._handle_event,
        )

        await self.websocket.run()

    async def run_async(self):
        await self.start()

    def run(self):
        asyncio.run(
            self.start()
        )

    async def close(self):
        if self.websocket:
            await self.websocket.close()