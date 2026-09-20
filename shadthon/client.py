from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Awaitable

from .exceptions import AuthenticationError
from .models import (
    FileInfo,
    LoginResult,
    Message,
    Poll,
    User,
)
from .session import Session


MessageHandler = Callable[[Message], Awaitable[Any]]


class Client:
    def __init__(
        self,
        phone_number: str | None = None,
        session_dir: str = "sessions",
        session_name: str = "default",
    ):
        self.phone_number = self._normalize_phone(phone_number)

        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.session_path = (
            self.session_dir /
            f"{session_name}.json"
        )

        self.session = Session.load(
            self.session_path
        )

        if self.phone_number:
            self.session.phone_number = (
                self.phone_number
            )

        self._message_handlers: list[
            MessageHandler
        ] = []

    @staticmethod
    def _normalize_phone(
        phone: str | None,
    ) -> str | None:
        if phone is None:
            return None

        phone = (
            phone
            .strip()
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        if phone.startswith("+"):
            phone = phone[1:]

        if phone.startswith("0"):
            phone = "98" + phone[1:]

        return phone

    def save_session(self) -> None:
        self.session.save(
            self.session_path
        )

    def is_authenticated(self) -> bool:
        return bool(
            self.session.auth
            and self.session.state == "authenticated"
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

    async def send_code(self) -> str:
        raise AuthenticationError(
            "Shad v6 sendCode is not implemented yet. "
            "The exact encrypted protocol response must "
            "be verified before sending authentication data."
        )

    async def login(
        self,
        otp: str,
        phone_code_hash: str | None = None,
    ) -> LoginResult:
        if not self.phone_number:
            raise AuthenticationError(
                "phone_number is required."
            )

        if not otp:
            raise AuthenticationError(
                "OTP code is required."
            )

        raise AuthenticationError(
            "Shad v6 signIn is not implemented yet. "
            "The exact encrypted protocol envelope must "
            "be verified before authentication."
        )

    async def send_message(
        self,
        chat_guid: str,
        text: str,
        reply_to_message_id: int | str | None = None,
    ) -> dict[str, Any]:
        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated."
            )

        raise NotImplementedError(
            "Shad sendMessage transport is not implemented yet."
        )

    async def get_messages(
        self,
        chat_guid: str,
        middle_message_id: int | str | None = None,
    ) -> list[Message]:
        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated."
            )

        raise NotImplementedError(
            "Shad message retrieval is not implemented yet."
        )

    async def get_message(
        self,
        chat_guid: str,
        message_id: int | str,
    ) -> Message | None:
        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated."
            )

        raise NotImplementedError(
            "Shad message retrieval is not implemented yet."
        )

    async def send_photo(
        self,
        chat_guid: str,
        file_path: str,
        caption: str | None = None,
    ) -> FileInfo:
        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated."
            )

        raise NotImplementedError(
            "Shad photo upload is not implemented yet."
        )

    async def send_video(
        self,
        chat_guid: str,
        file_path: str,
        caption: str | None = None,
    ) -> FileInfo:
        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated."
            )

        raise NotImplementedError(
            "Shad video upload is not implemented yet."
        )

    async def send_file(
        self,
        chat_guid: str,
        file_path: str,
        caption: str | None = None,
    ) -> FileInfo:
        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated."
            )

        raise NotImplementedError(
            "Shad file upload is not implemented yet."
        )

    async def upload_file(
        self,
        file_path: str,
    ) -> FileInfo:
        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated."
            )

        raise NotImplementedError(
            "Shad file upload is not implemented yet."
        )

    async def download_file(
        self,
        file_info: FileInfo,
        destination: str,
    ) -> str:
        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated."
            )

        raise NotImplementedError(
            "Shad file download is not implemented yet."
        )

    async def get_poll(
        self,
        poll_id: str | int,
    ) -> Poll:
        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated."
            )

        raise NotImplementedError(
            "Shad poll API is not implemented yet."
        )

    async def vote_poll(
        self,
        poll_id: str | int,
        selection_index: int,
    ) -> dict[str, Any]:
        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated."
            )

        raise NotImplementedError(
            "Shad poll API is not implemented yet."
        )

    async def start(self) -> None:
        raise NotImplementedError(
            "Automatic update polling will be added "
            "after the exact Shad update protocol is verified."
        )

    run = start