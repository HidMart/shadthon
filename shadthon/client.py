import json
import asyncio

from .session import Session
from .auth import AuthManager
from .transport import Transport
from .models import Message


class Client:
    def __init__(
        self,
        auth=None,
        session_name="shadthon",
        base_url=None
    ):
        self.session = Session(
            session_name
        )

        self.session.load()

        if auth:
            self.session.auth = auth
            self.session.save()

        self.base_url = base_url

        self._message_handler = None

        self.transport = Transport(
            auth=self.session.auth,
            private_key=self.session.private_key,
            tmp_session=self.session.tmp_session,
            base_url=(
                base_url
                or "https://shadmessenger36.iranlms.ir/"
            )
        )

    def on_message(self, func=None):
        if func is not None:
            self._message_handler = func
            return func

        def decorator(callback):
            self._message_handler = callback
            return callback

        return decorator

    @property
    def authenticated(self):
        return self.session.authenticated

    async def request(
        self,
        method,
        input_data=None
    ):
        self.transport.auth = (
            self.session.auth
        )

        self.transport.private_key = (
            self.session.private_key
        )

        self.transport.tmp_session = (
            self.session.tmp_session
        )

        return await self.transport.request(
            method,
            input_data,
            authenticated=self.authenticated
        )

    async def send_message(
        self,
        object_guid,
        text,
        reply_to_message_id=None
    ):
        data = {
            "object_guid": object_guid,
            "text": text
        }

        if reply_to_message_id:
            data[
                "reply_to_message_id"
            ] = reply_to_message_id

        return await self.request(
            "sendMessage",
            data
        )

    async def get_messages(
        self,
        object_guid,
        max_id=0,
        limit=20
    ):
        return await self.request(
            "getMessages",
            {
                "object_guid": object_guid,
                "max_id": max_id,
                "limit": limit
            }
        )

    async def send_chat_activity(
        self,
        object_guid,
        activity="Typing"
    ):
        return await self.request(
            "sendChatActivity",
            {
                "object_guid": object_guid,
                "activity": activity
            }
        )

    async def login(
        self,
        phone_number
    ):
        auth = AuthManager(
            self.session,
            self.base_url
        )

        await auth.start()

        return await auth.send_code(
            phone_number
        )

    async def verify(
        self,
        code
    ):
        auth = AuthManager(
            self.session,
            self.base_url
        )

        result = await auth.sign_in(
            code
        )

        if self.session.auth:
            await auth.register_device()

        self.transport.auth = (
            self.session.auth
        )

        self.transport.private_key = (
            self.session.private_key
        )

        return result

    async def run(self):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated"
            )

        while True:
            await asyncio.sleep(30)