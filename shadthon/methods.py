import random

from .crypto import (
    decode_auth,
    derive_key,
    generate_rsa_keys,
    rsa_decrypt,
)
from .utils import (
    generate_session_id,
    split_phone,
)


class Methods:
    def __init__(
        self,
        transport,
        session,
        store,
    ):
        self.transport = transport
        self.session = session
        self.store = store

    async def request_code(
        self,
        phone_number: str,
    ):
        subscriber, country = split_phone(
            phone_number
        )

        full_phone = (
            f"{country}{subscriber}"
        )

        temporary = generate_session_id()

        self.session.phone_number = phone_number
        self.session.temporary_session = temporary
        self.session.set_key(
            derive_key(temporary)
        )
        self.session.set_iv(
            b"\x00" * 16
        )

        self.store.save(self.session)

        response = await self.transport.send_handshake(
            "sendCode",
            {
                "phone_number": full_phone,
                "send_type": "SMS",
            },
        )

        phone_code_hash = (
            response.get("phone_code_hash")
            or response.get("data", {}).get(
                "phone_code_hash",
                "",
            )
        )

        if not phone_code_hash:
            raise RuntimeError(
                "Shad did not return phone_code_hash."
            )

        return {
            "phone_number": full_phone,
            "phone_code_hash": phone_code_hash,
            "response": response,
        }

    async def sign_in(
        self,
        phone_number: str,
        otp: str,
        phone_code_hash: str,
    ):
        subscriber, country = split_phone(
            phone_number
        )

        full_phone = (
            f"{country}{subscriber}"
        )

        public_key, private_key = (
            generate_rsa_keys()
        )

        self.session.private_key_pem = (
            private_key
        )

        response = await self.transport.send_handshake(
            "signIn",
            {
                "phone_code": str(otp),
                "phone_number": full_phone,
                "phone_code_hash": phone_code_hash,
                "public_key": public_key,
            },
        )

        raw_auth = (
            response.get("auth")
            or response.get("data", {}).get(
                "auth",
                "",
            )
        )

        user_data = (
            response.get("user")
            or response.get("data", {}).get(
                "user",
                {},
            )
            or {}
        )

        if not raw_auth:
            raise RuntimeError(
                "Shad did not return authentication data."
            )

        decrypted_auth = rsa_decrypt(
            private_key,
            raw_auth,
        )

        permanent_key = derive_key(
            decrypted_auth
        )

        self.session.auth = decrypted_auth
        self.session.decoded_auth = (
            decode_auth(decrypted_auth)
        )

        self.session.set_key(
            permanent_key
        )

        self.session.set_iv(
            b"\x00" * 16
        )

        self.session.user_guid = (
            user_data.get(
                "user_guid",
                "",
            )
        )

        self.session.state = 1

        self.store.save(self.session)

        await self.register_device()

        return response

    async def register_device(self):
        return await self.transport.send_authenticated(
            "registerDevice",
            {
                "app_version": "WB_4.4.26",
                "device_hash": "".join(
                    random.choices(
                        "0123456789",
                        k=26,
                    )
                ),
                "device_model": "Chrome 153",
                "is_multi_account": False,
                "lang_code": "fa",
                "system_version": "Web",
                "token": "",
                "token_type": "Web",
            },
        )