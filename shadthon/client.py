from __future__ import annotations

from pathlib import Path

from .exceptions import AuthenticationError
from .media import MediaManager
from .messages import MessageManager
from .models import LoginResult, User
from .polls import PollManager
from .session import Session, SessionStore
from .transport import Transport
from .utils import normalize_phone


class Client:

    def __init__(
        self,
        phone_number: str | None = None,
        session_dir: str = "sessions",
    ):
        self.phone_number = (
            normalize_phone(phone_number)
            if phone_number
            else None
        )

        self.sessions = SessionStore(
            session_dir
        )

        self.session = (
            self.sessions.load(
                self.phone_number
            )
            if self.phone_number
            else None
        )

        if self.session is None:
            self.session = Session(
                phone_number=self.phone_number
            )

        self.transport = Transport(
            self.session
        )

        self.messages = MessageManager(
            self.transport
        )

        self.media = MediaManager(
            self.transport
        )

        self.polls = PollManager(
            self.transport
        )

    async def send_code(self):
        if not self.phone_number:
            raise AuthenticationError(
                "Phone number is required"
            )

        from .auth import AuthManager

        return await AuthManager(
            self
        ).request_code()

    async def login(
        self,
        otp: str,
        phone_code_hash: str,
    ) -> LoginResult:

        from .auth import AuthManager

        result = await AuthManager(
            self
        ).login(
            otp,
            phone_code_hash,
        )

        self.sessions.save(
            self.session
        )

        return result

    async def send_message(
        self,
        chat_guid: str,
        text: str,
        reply_to: str | None = None,
    ):
        return await self.messages.send_message(
            chat_guid,
            text,
            reply_to,
        )

    async def get_messages(
        self,
        chat_guid: str,
        middle_message_id: str = "0",
    ):
        return await self.messages.get_messages(
            chat_guid,
            middle_message_id,
        )

    async def get_message(
        self,
        chat_guid: str,
        message_id: str,
    ):
        return await self.messages.get_message(
            chat_guid,
            message_id,
        )

    async def send_photo(
        self,
        chat_guid: str,
        file_path: str,
        caption: str | None = None,
    ):
        return await self.media.send_photo(
            chat_guid,
            file_path,
            caption,
        )

    async def send_video(
        self,
        chat_guid: str,
        file_path: str,
        caption: str | None = None,
    ):
        return await self.media.send_video(
            chat_guid,
            file_path,
            caption,
        )

    async def send_file(
        self,
        chat_guid: str,
        file_path: str,
        caption: str | None = None,
    ):
        return await self.media.send_file(
            chat_guid,
            file_path,
            caption,
        )

    async def upload_file(
        self,
        file_path: str,
    ):
        return await self.media.upload_file(
            file_path
        )

    async def download_file(
        self,
        file_info,
        output_path: str,
    ):
        return await self.media.download_file(
            file_info,
            output_path,
        )

    async def get_poll(
        self,
        poll_id: str,
    ):
        return await self.polls.get_poll(
            poll_id
        )

    async def vote_poll(
        self,
        poll_id: str,
        option: int,
    ):
        return await self.polls.vote_poll(
            poll_id,
            option,
        )

    def is_authenticated(self) -> bool:
        return bool(
            self.session.auth
            and self.session.state
            == "authenticated"
        )

    def logout(self) -> None:
        if self.phone_number:
            self.sessions.delete(
                self.phone_number
            )

        self.session = Session(
            phone_number=self.phone_number
        )

    async def start(self):
        if not self.is_authenticated():
            raise AuthenticationError(
                "Client is not authenticated"
            )

        return self