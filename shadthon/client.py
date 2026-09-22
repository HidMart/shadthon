from __future__ import annotations

import asyncio

from .auth import AuthManager
from .dispatcher import Dispatcher
from .methods import Methods
from .session import Session
from .transport import Transport
from .types import Chat, Message, User


class Client:
    def __init__(
        self,
        session_name="default",
        phone=None,
        base_url="https://shadmessenger36.iranlms.ir",
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

        self.base_url = base_url.rstrip("/")

        self.auth = auth or self.session.auth

        self.transport = Transport(
            base_url=self.base_url,
            auth=self.auth,
            private_key=self.session.private_key,
        )

        self.auth_manager = AuthManager(
            self.transport,
            self.session,
        )

        self.methods = Methods(self.transport)
        self.dispatcher = Dispatcher()

        self._running = False
        self._connected = False
        self._poll_task = None
        self._seen_messages = set()

    @property
    def is_connected(self):
        return self._connected

    @property
    def authenticated(self):
        return bool(self.session.auth)

    async def connect(self):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated"
            )

        self.transport.auth = self.session.auth
        self.transport.private_key = (
            self.session.private_key
        )

        self._connected = True
        return True

    async def disconnect(self):
        self._running = False

        if self._poll_task is not None:
            self._poll_task.cancel()

            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

            self._poll_task = None

        self._connected = False
        await self.transport.close()

    async def start(self):
        if not self._connected:
            await self.connect()

        self._running = True
        await self._poll_messages()

    async def start_in_background(self):
        if not self._connected:
            await self.connect()

        if self._poll_task is None:
            self._running = True
            self._poll_task = asyncio.create_task(
                self._poll_messages()
            )

        return self._poll_task

    async def run_until_disconnected(self):
        await self.start()

    async def stop(self):
        await self.disconnect()

    async def get_me(self):
        result = await self.invoke("getMe")
        return self._to_user(result)

    async def get_user_info(self, user_guid):
        result = await self.invoke(
            "getUserInfo",
            user_guid=str(user_guid),
        )

        return self._to_user(result)

    async def get_chats(self):
        result = await self.methods.get_chats()

        if isinstance(result, list):
            return [
                Chat.from_dict(
                    item,
                    client=self,
                )
                for item in result
            ]

        return result

    async def get_chat_info(self, object_guid):
        result = await self.invoke(
            "getChatInfo",
            object_guid=str(object_guid),
        )

        if isinstance(result, dict):
            return Chat.from_dict(
                result,
                client=self,
            )

        return result

    async def get_chat_history(
        self,
        object_guid,
        limit=50,
    ):
        return await self.get_messages(
            object_guid,
            limit=limit,
        )

    async def get_messages(
        self,
        object_guid,
        limit=50,
    ):
        return await self.methods.get_messages(
            object_guid,
            limit=limit,
        )

    async def send_message(
        self,
        object_guid,
        text,
        reply_to_message_id=None,
    ):
        return await self.methods.send_message(
            object_guid,
            text,
            reply_to_message_id,
        )

    async def edit_message(
        self,
        object_guid,
        message_id,
        text,
    ):
        return await self.methods.edit_message(
            object_guid,
            message_id,
            text,
        )

    async def delete_message(
        self,
        object_guid,
        message_id,
    ):
        return await self.methods.delete_message(
            object_guid,
            message_id,
        )

    async def delete_messages(
        self,
        object_guid,
        message_ids,
    ):
        return await self.methods.delete_messages(
            object_guid,
            message_ids,
        )

    async def upload_file(self, file):
        raise NotImplementedError(
            "The Shad upload protocol has not "
            "been verified yet."
        )

    async def send_photo(
        self,
        object_guid,
        photo,
        caption="",
        reply_to_message_id=None,
    ):
        uploaded = await self.upload_file(photo)

        return await self.invoke(
            "sendPhoto",
            object_guid=str(object_guid),
            file=uploaded,
            caption=caption,
            reply_to_message_id=(
                str(reply_to_message_id)
                if reply_to_message_id is not None
                else None
            ),
        )

    async def send_file(
        self,
        object_guid,
        file,
        caption="",
        reply_to_message_id=None,
    ):
        uploaded = await self.upload_file(file)

        return await self.invoke(
            "sendFile",
            object_guid=str(object_guid),
            file=uploaded,
            caption=caption,
            reply_to_message_id=(
                str(reply_to_message_id)
                if reply_to_message_id is not None
                else None
            ),
        )

    async def update_profile(
        self,
        first_name=None,
        last_name=None,
        bio=None,
    ):
        return await self.invoke(
            "updateProfile",
            first_name=first_name,
            last_name=last_name,
            bio=bio,
        )

    async def block_user(self, user_guid):
        return await self.invoke(
            "blockUser",
            user_guid=str(user_guid),
        )

    async def unblock_user(self, user_guid):
        return await self.invoke(
            "unblockUser",
            user_guid=str(user_guid),
        )

    async def register_device(self):
        return await self.methods.register_device()

    async def get_chats_updates(self, state=0):
        return await self.methods.get_chats_updates(state)

    async def get_messages_updates(
        self,
        object_guid,
        state=0,
    ):
        return await self.methods.get_messages_updates(
            object_guid,
            state,
        )

    async def invoke(self, method, **kwargs):
        return await self.methods.invoke(
            method,
            **kwargs,
        )

    def on_message(self, filter_=None):
        def decorator(func):
            self.dispatcher.add_handler(
                func,
                filter_,
            )
            return func

        return decorator

    async def _poll_messages(self, interval=2):
        while self._running:
            try:
                result = await self.get_chats_updates()

                for raw in self._extract_messages(result):
                    message = Message.from_dict(
                        raw,
                        client=self,
                    )

                    key = (
                        message.object_guid,
                        message.id,
                    )

                    if key in self._seen_messages:
                        continue

                    self._seen_messages.add(key)

                    await self.dispatcher.dispatch(
                        message
                    )

            except asyncio.CancelledError:
                raise

            except Exception:
                pass

            await asyncio.sleep(interval)

    def _extract_messages(self, value):
        result = []

        if isinstance(value, dict):
            if (
                "message_id" in value
                or "messageId" in value
            ):
                result.append(value)

            for item in value.values():
                result.extend(
                    self._extract_messages(item)
                )

        elif isinstance(value, list):
            for item in value:
                result.extend(
                    self._extract_messages(item)
                )

        return result

    def _to_user(self, result):
        if isinstance(result, User):
            return result

        if isinstance(result, dict):
            return User.from_dict(result)

        return User(raw=result)