from __future__ import annotations

from pathlib import Path
from typing import Any, Awaitable, Callable

from .auth import AuthManager
from .exceptions import AuthenticationError
from .models import (
    Message,
    Poll,
    LoginResult,
)
from .session import Session
from .transport import Transport
from .utils import normalize_phone


MessageHandler = Callable[
    [Message],
    Awaitable[Any],
]


class Client:

    def __init__(
        self,
        phone_number: str | None = None,
        session_dir: str = "sessions",
        session_name: str = "default",
        messenger_host: str | None = None,
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
                normalize_phone(phone_number)
            )

        if messenger_host:
            self.session.messenger_host = (
                messenger_host
            )

        self.transport = Transport(
            self.session,
            timeout=timeout,
        )

        self.auth = AuthManager(
            self
        )

        self._message_handlers: list[
            MessageHandler
        ] = []

        self.save_session()

    @property
    def phone_number(self) -> str | None:
        return self.session.phone_number

    @phone_number.setter
    def phone_number(
        self,
        value: str | None,
    ) -> None:
        self.session.phone_number = (
            normalize_phone(value)
            if value
            else None
        )

    def save_session(self) -> None:
        self.session.save(
            self.session_path
        )

    def is_authenticated(self) -> bool:
        return bool(
            self.session.auth
            and self.session.state
            == "authenticated"
        )

    def logout(self) -> None:
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
            await handler(message)

    async def send_code(self) -> dict:
        return await self.auth.request_code()

    async def login(
        self,
        otp: str,
        phone_code_hash: str | None = None,
    ) -> LoginResult:

        return await self.auth.login(
            otp,
            phone_code_hash,
        )

    async def call(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:

        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated."
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
            "object_guid": chat_guid,
            "rnd": __import__(
                "random"
            ).randint(
                100000000,
                999999999,
            ),
            "text": text,
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

        data: dict[str, Any] = {
            "object_guid": chat_guid,
        }

        if middle_message_id is not None:
            data[
                "middle_message_id"
            ] = middle_message_id

        result = await self.call(
            "getMessagesInterval",
            data,
        )

        raw_messages = result.get(
            "messages",
            result.get(
                "data",
                [],
            ),
        )

        if not isinstance(
            raw_messages,
            list,
        ):
            return []

        return [
            Message(
                message_id=item.get(
                    "message_id"
                ),
                object_guid=item.get(
                    "object_guid"
                ),
                text=item.get(
                    "text"
                ),
                sender_guid=item.get(
                    "sender_guid"
                ),
                raw=item,
            )
            for item in raw_messages
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
                "object_guid": chat_guid,
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

        return Message(
            message_id=item.get(
                "message_id"
            ),
            object_guid=item.get(
                "object_guid"
            ),
            text=item.get(
                "text"
            ),
            sender_guid=item.get(
                "sender_guid"
            ),
            raw=item,
        )

    async def get_poll(
        self,
        poll_id: str | int,
    ) -> Poll:

        result = await self.call(
            "getPollStatus",
            {
                "poll_id": poll_id,
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
                data.get("poll_id")
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
                "poll_id": poll_id,
                "selection_index":
                    selection_index,
            },
        )

    async def start(self) -> None:
        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated."
            )

    async def run(self) -> None:
        await self.start()