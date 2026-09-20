from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Awaitable, Callable

from .auth import AuthManager
from .exceptions import AuthenticationError
from .models import (
    LoginResult,
    Message,
    Poll,
)
from .session import Session
from .transport import Transport
from .websocket import ShadWebSocket


MessageHandler = Callable[
    [Message],
    Awaitable[Any],
]


class Client:

    def __init__(
        self,
        auth: str | None = None,
        phone_number: str | None = None,
        session_dir: str = "sessions",
        session_name: str = "default",
        timeout: int = 30,
    ):

        self.session_dir = Path(
            session_dir
        )

        self.session_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.session_path = (
            self.session_dir
            / f"{session_name}.json"
        )

        self.session = Session.load(
            self.session_path
        )

        if phone_number:
            self.session.phone_number = (
                phone_number
            )

        self.transport = Transport(
            self.session,
            timeout=timeout,
        )

        self.auth = AuthManager(
            self
        )

        self.websocket = ShadWebSocket(
            self.session,
            self.transport,
        )

        self._message_handlers: list[
            MessageHandler
        ] = []

        if auth:
            self.session.set_auth(
                auth.strip()
            )

        self.save_session()

    @property
    def phone_number(
        self,
    ) -> str | None:

        return self.session.phone_number

    @property
    def auth_token(
        self,
    ) -> str | None:

        return self.session.auth

    def save_session(
        self,
    ) -> None:

        self.session.save(
            self.session_path
        )

    def is_authenticated(
        self,
    ) -> bool:

        return bool(
            self.session.auth
            and self.session.state
            == "authenticated"
        )

    def set_auth(
        self,
        auth: str,
    ) -> LoginResult:

        return self.auth.set_auth(
            auth
        )

    def logout(
        self,
    ) -> None:

        self.session.clear(
            self.session_path
        )

    def on_message(
        self,
        handler: MessageHandler,
    ) -> MessageHandler:

        self._message_handlers.append(
            handler
        )

        return handler

    async def dispatch_message(
        self,
        message: Message,
    ) -> None:

        for handler in list(
            self._message_handlers
        ):
            try:
                result = handler(
                    message
                )

                if result is not None:
                    await result

            except Exception as exc:
                print(
                    "Shadthon handler error:",
                    exc,
                )

    def _message_from_update(
        self,
        update: dict[str, Any],
    ) -> Message:

        message = update

        if isinstance(
            update.get("message"),
            dict,
        ):
            message = update["message"]

        text = message.get(
            "text"
        )

        if text is None:

            nested = message.get(
                "message"
            )

            if isinstance(
                nested,
                dict,
            ):
                text = nested.get(
                    "text"
                )

        message_id = (
            message.get(
                "message_id"
            )
            or message.get(
                "id"
            )
        )

        object_guid = (
            message.get(
                "object_guid"
            )
            or message.get(
                "chat_id"
            )
        )

        sender_guid = (
            message.get(
                "sender_guid"
            )
            or message.get(
                "author_object_guid"
            )
        )

        return Message(
            message_id=message_id,
            object_guid=object_guid,
            text=text,
            sender_guid=sender_guid,
            raw=update,
        )

    async def call(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:

        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated. "
                "Set a valid Shad auth token first."
            )

        return await self.transport.authenticated(
            method,
            input_data,
        )

    async def send_message(
        self,
        chat_guid: str,
        text: str,
        reply_to_message_id:
            int | str | None = None,
    ) -> dict[str, Any]:

        data: dict[str, Any] = {
            "object_guid":
                chat_guid,
            "rnd":
                random.randint(
                    100000000,
                    999999999,
                ),
            "text":
                text,
        }

        if reply_to_message_id is not None:
            data[
                "reply_to_message_id"
            ] = reply_to_message_id

        return await self.call(
            "sendMessage",
            data,
        )

    async def get_messages(
        self,
        chat_guid: str,
        middle_message_id:
            int | str | None = None,
    ) -> list[Message]:

        data = {
            "object_guid":
                chat_guid,
        }

        if middle_message_id is not None:
            data[
                "middle_message_id"
            ] = middle_message_id

        result = await self.call(
            "getMessagesInterval",
            data,
        )

        raw = result.get(
            "messages",
            result.get(
                "data",
                [],
            ),
        )

        if not isinstance(
            raw,
            list,
        ):
            return []

        return [
            self._message_from_update(
                item
            )
            for item in raw
            if isinstance(
                item,
                dict,
            )
        ]

    async def get_message(
        self,
        chat_guid: str,
        message_id: int | str,
    ) -> Message | None:

        result = await self.call(
            "getMessagesByID",
            {
                "object_guid":
                    chat_guid,
                "message_ids": [
                    message_id
                ],
            },
        )

        messages = result.get(
            "messages",
            result.get(
                "data",
                [],
            ),
        )

        if not isinstance(
            messages,
            list,
        ) or not messages:

            return None

        item = messages[0]

        if not isinstance(
            item,
            dict,
        ):
            return None

        return self._message_from_update(
            item
        )

    async def get_poll(
        self,
        poll_id: str | int,
    ) -> Poll:

        result = await self.call(
            "getPollStatus",
            {
                "poll_id":
                    poll_id,
            },
        )

        data = result.get(
            "poll",
            result.get(
                "data",
                result,
            ),
        )

        if not isinstance(
            data,
            dict,
        ):
            data = {}

        return Poll(
            poll_id=(
                data.get(
                    "poll_id"
                )
                or poll_id
            ),
            question=data.get(
                "question"
            ),
            options=data.get(
                "options",
                [],
            ),
            raw=data,
        )

    async def vote_poll(
        self,
        poll_id: str | int,
        selection_index: int,
    ) -> dict[str, Any]:

        return await self.call(
            "votePoll",
            {
                "poll_id":
                    poll_id,
                "selection_index":
                    selection_index,
            },
        )

    async def run(
        self,
    ) -> None:

        if not self.is_authenticated():
            raise AuthenticationError(
                "Set a valid Shad auth token first."
            )

        async for update in (
            self.websocket.updates(
                message_updates=True
            )
        ):

            message = (
                self._message_from_update(
                    update
                )
            )

            await self.dispatch_message(
                message
            )

    async def start(
        self,
    ) -> None:

        await self.run()