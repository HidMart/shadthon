from __future__ import annotations

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

    async def request_code(
        self,
    ) -> str:

        phone = normalize_phone(
            self.client.phone_number
        )

        if not phone:
            raise AuthenticationError(
                "phone_number is required."
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
            {},
        )

        if not isinstance(
            data,
            dict,
        ):
            data = {}

        phone_code_hash = (
            data.get("phone_code_hash")
            or result.get("phone_code_hash")
        )

        if not phone_code_hash:
            status = result.get(
                "status"
            )

            detail = result.get(
                "status_det"
            )

            raise AuthenticationError(
                "Shad did not return "
                "phone_code_hash. "
                f"status={status!r}, "
                f"status_det={detail!r}"
            )

        self.client.session.phone_code_hash = (
            str(phone_code_hash)
        )

        self.client.save_session()

        return str(
            phone_code_hash
        )

    async def login(
        self,
        otp: str,
        phone_code_hash: str | None = None,
    ) -> LoginResult:

        phone = normalize_phone(
            self.client.phone_number
        )

        if not phone:
            raise AuthenticationError(
                "phone_number is required."
            )

        if not otp:
            raise AuthenticationError(
                "OTP code is required."
            )

        phone_code_hash = (
            phone_code_hash
            or self.client.session.phone_code_hash
        )

        if not phone_code_hash:
            raise AuthenticationError(
                "phone_code_hash is required."
            )

        private_pem, public_pem = (
            generate_rsa_keypair()
        )

        self.client.session.private_key_pem = (
            private_pem
        )

        self.client.session.public_key_pem = (
            public_pem
        )

        result = await self.client.transport.handshake(
            "signIn",
            {
                "phone_code":
                    str(otp),
                "phone_number":
                    phone,
                "phone_code_hash":
                    str(phone_code_hash),
                "public_key":
                    public_pem,
            },
        )

        data = result.get(
            "data",
            {},
        )

        if not isinstance(
            data,
            dict,
        ):
            data = {}

        raw_auth = (
            data.get("auth")
            or result.get("auth")
        )

        if not raw_auth:
            raise AuthenticationError(
                "Shad did not return authentication data."
            )

        decrypted_auth = (
            raw_auth
        )

        try:
            decrypted_auth = (
                rsa_oaep_decrypt(
                    str(raw_auth),
                    private_pem,
                ).decode(
                    "utf-8",
                    errors="ignore",
                )
            )
        except Exception:
            pass

        self.client.session.auth = (
            decrypted_auth
        )

        decoded = decode_auth(
            decrypted_auth
        )

        self.client.session.decoded_auth = (
            decoded
        )

        key, iv = derive_key(
            decrypted_auth,
            decoded,
        )

        self.client.session.set_key(
            key
        )

        self.client.session.set_iv(
            iv
        )

        self.client.session.state = (
            "authenticated"
        )

        user_data = data.get(
            "user"
        )

        user = None

        if isinstance(
            user_data,
            dict,
        ):
            user = User.from_dict(
                user_data
            )

        self.client.save_session()

        return LoginResult(
            user=user,
            auth=decrypted_auth,
            raw=result,
        )