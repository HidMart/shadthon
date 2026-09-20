from .crypto import (
    generate_tmp_session,
    generate_rsa_keys,
    decrypt_rsa_oaep,
    auth_set,
)
from .transport import Transport


class AuthManager:
    def __init__(
        self,
        session,
        base_url=None
    ):
        self.session = session

        self.transport = Transport(
            tmp_session=session.tmp_session,
            base_url=base_url
                if base_url
                else Transport.__init__.__defaults__[0]
        )

    async def start(self):
        self.session.tmp_session = (
            generate_tmp_session()
        )

        public_key, private_key = (
            generate_rsa_keys()
        )

        self.session.public_key = public_key
        self.session.private_key = private_key

        self.transport.tmp_session = (
            self.session.tmp_session
        )

        self.session.save()

    async def send_code(
        self,
        phone_number: str,
        send_type: str = "SMS",
        pass_key: str | None = None
    ):
        if not self.session.tmp_session:
            await self.start()

        self.session.phone_number = (
            phone_number
        )

        data = {
            "phone_number": phone_number,
            "send_type": send_type
        }

        if pass_key:
            data["pass_key"] = pass_key

        result = await self.transport.request(
            "sendCode",
            data,
            authenticated=False
        )

        if result.get("phone_code_hash"):
            self.session.phone_code_hash = (
                result["phone_code_hash"]
            )
            self.session.save()

        return result

    async def sign_in(
        self,
        phone_code: str
    ):
        if not self.session.phone_code_hash:
            raise RuntimeError(
                "phone_code_hash is missing"
            )

        result = await self.transport.request(
            "signIn",
            {
                "phone_number":
                    self.session.phone_number,
                "phone_code_hash":
                    self.session.phone_code_hash,
                "phone_code":
                    phone_code,
                "public_key":
                    self.session.public_key,
            },
            authenticated=False
        )

        data = result.get("data", result)

        encrypted_auth = data.get(
            "auth"
        )

        if not encrypted_auth:
            return result

        auth = decrypt_rsa_oaep(
            self.session.private_key,
            encrypted_auth
        )

        self.session.auth = auth
        self.session.save()

        return result

    async def register_device(
        self,
        device_hash="",
        device_model="Shadthon",
        system_version="Python",
        token=""
    ):
        if not self.session.auth:
            raise RuntimeError(
                "Authentication required"
            )

        self.transport.auth = (
            self.session.auth
        )

        self.transport.private_key = (
            self.session.private_key
        )

        result = await self.transport.request(
            "registerDevice",
            {
                "app_version": "4.4.26",
                "device_hash": device_hash,
                "device_model": device_model,
                "is_multi_account": False,
                "lang_code": "fa",
                "system_version": system_version,
                "token": token,
                "token_type": "Firebase",
            },
            authenticated=True
        )

        self.session.save()

        return result