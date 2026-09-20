from __future__ import annotations

import base64
import json

from .crypto import (
    decode_auth,
    derive_key,
    generate_rsa_keypair,
    rsa_oaep_decrypt,
)
from .exceptions import AuthenticationError
from .models import LoginResult, User
from .utils import normalize_phone


class AuthManager:

    def __init__(self, client):
        self.client = client

    async def request_code(self):

        phone = normalize_phone(
            self.client.phone_number
        )

        self.client.session.phone_number = phone

        result = await self.client.transport.handshake(
            "sendCode",
            {
                "phone_number": phone,
                "send_type": "SMS",
            },
        )

        data = result.get(
            "data",
            result,
        )

        phone_code_hash = (
            data.get("phone_code_hash")
            or result.get("phone_code_hash")
        )

        if not phone_code_hash:
            raise AuthenticationError(
                "Shad did not return phone_code_hash"
            )

        return phone_code_hash

    async def login(
        self,
        otp: str,
        phone_code_hash: str,
    ) -> LoginResult:

        phone = normalize_phone(
            self.client.phone_number
        )

        private_pem, public_pem = (
            generate_rsa_keypair()
        )

        self.client.session.private_key_pem = (
            private_pem
        )

        result = await self.client.transport.handshake(
            "signIn",
            {
                "phone_code": otp,
                "phone_number": phone,
                "phone_code_hash": phone_code_hash,
                "public_key": public_pem,
            },
        )

        data = result.get(
            "data",
            result,
        )

        auth = (
            data.get("auth")
            or result.get("auth")
        )

        if not auth:
            raise AuthenticationError(
                "Shad did not return auth"
            )

        self.client.session.auth = auth

        decoded = decode_auth(
            auth
        )

        self.client.session.decoded_auth = (
            decoded
        )

        key, iv = derive_key(
            auth,
            decoded,
        )

        self.client.session.key_hex = (
            key.hex()
        )

        self.client.session.iv_hex = (
            iv.hex()
        )

        self.client.session.state = (
            "authenticated"
        )

        user_data = data.get(
            "user"
        )

        user = (
            User.from_dict(user_data)
            if isinstance(
                user_data,
                dict,
            )
            else None
        )

        return LoginResult(
            user=user,
            auth=auth,
            raw=result,
        )