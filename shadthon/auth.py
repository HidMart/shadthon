from __future__ import annotations

from .exceptions import AuthenticationError
from .models import LoginResult


class AuthManager:

    def __init__(self, client):
        self.client = client

    def set_auth(
        self,
        auth: str,
    ) -> LoginResult:

        if not isinstance(
            auth,
            str,
        ) or not auth.strip():

            raise AuthenticationError(
                "A valid Shad auth token is required."
            )

        auth = auth.strip()

        self.client.session.set_auth(
            auth
        )

        self.client.save_session()

        return LoginResult(
            auth=auth
        )

    async def request_code(self):
        raise AuthenticationError(
            "OTP login is not implemented for "
            "the verified Shad v5 account protocol. "
            "Use a valid Shad Web auth token."
        )

    async def login(
        self,
        otp: str,
        phone_code_hash: str | None = None,
    ):

        raise AuthenticationError(
            "OTP login is not implemented for "
            "the verified Shad v5 account protocol."
        )