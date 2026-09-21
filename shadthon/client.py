from __future__ import annotations

import asyncio

from .auth import AuthManager
from .dispatcher import Dispatcher
from .models import Message
from .session import Session
from .transport import Transport
from .methods import Methods


class Client:
    def __init__(
        self,
        session_name="default",
        phone=None,
        base_url=None,
        session=None,
    ):
        self.session = (
            session
            if isinstance(session, Session)
            else Session(session_name)
        )

        if phone:
            self.session.data["phone_number"] = phone

        if base_url:
            host = (
                base_url
                .replace("https://", "")
                .replace("http://", "")
                .rstrip("/")
            )
            self.session.messenger_host = host

        self.transport = Transport(self.session)

        self.methods = Methods(
            self.session,
            self.transport,
            client=self,
        )

        self.auth_manager = AuthManager(
            self.transport,
            self.session,
        )

        self.dispatcher = Dispatcher(self)

    @property
    def authenticated(self):
        return self.session.authenticated

    async def send_code(self, phone=None):
        phone = phone or self.session.phone

        if not phone:
            raise ValueError("Phone number is required.")

        return await self.auth_manager.send_code(phone)

    async def sign_in(
        self,
        phone=None,
        phone_code=None,
        phone_code_hash=None,
    ):
        phone = phone or self.session.phone

        if not phone:
            raise ValueError("Phone number is required.")

        if not phone_code:
            raise ValueError("Login code is required.")

        result = await self.auth_manager.sign_in(
            phone,
            phone_code,
            phone_code_hash,
        )

        try:
            register_result = await self.methods.register_device()

            register_data = register_result.get(
                "data",
                register_result,
            )

            register_status = register_data.get("status")

            if register_status not in (
                None,
                "OK",
                "SUCCESS",
            ):
                raise RuntimeError(
                    f"registerDevice failed: {register_data}"
                )

            self.session.data["device_registered"] = True
            self.session.save()

        except Exception:
            self.session.data["device_registered"] = False
            self.session.save()
            raise

        return result

    async def register_device(self):
        result = await self.methods.register_device()

        data = result.get("data", result)
        status = data.get("status")

        if status not in (None, "OK", "SUCCESS"):
            raise RuntimeError(
                f"registerDevice failed: {data}"
            )

        self.session.data["device_registered"] = True
        self.session.save()

        return result

    def on_message(self, handler=None):
        if handler is None:
            def decorator(func):
                self.dispatcher.register_handler(func)
                return func

            return decorator

        self.dispatcher.register_handler(handler)
        return handler

    def message_from_dict(self, data):
        return Message.from_dict(
            data,
            client=self,
        )

    async def send_message(
        self,
        object_guid,
        text="",
        reply_to_message_id=None,
        file_inline=None,
    ):
        return await self.methods.send_message(
            object_guid,
            text,
            reply_to_message_id,
            file_inline,
        )

    async def get_messages(
        self,
        object_guid,
        limit=50,
        sort="FromMax",
        max_id=None,
        min_id=None,
    ):
        return await self.methods.get_messages(
            object_guid,
            limit,
            sort,
            max_id,
            min_id,
        )

    async def get_chats_updates(self, state=None):
        return await self.methods.get_chats_updates(state)

    async def get_messages_updates(
        self,
        object_guid,
        state=None,
    ):
        return await self.methods.get_messages_updates(
            object_guid,
            state,
        )

    async def get_chats(self, start_id=None):
        return await self.methods.get_chats(start_id)

    async def start(self):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated. Login first."
            )

        self.dispatcher.start()

        try:
            while self.dispatcher.running:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            await self.stop()
            raise

    async def run_async(self):
        await self.start()

    def run(self):
        asyncio.run(self.start())

    async def stop(self):
        await self.dispatcher.stop()
        await self.transport.close()
        self.session.save()

    async def close(self):
        await self.stop()