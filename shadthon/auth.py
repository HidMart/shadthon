from .crypto import Crypto
from .exceptions import AuthenticationError


class AuthManager:
    def __init__(self, transport, session):
        self.transport = transport
        self.session = session

    async def send_code(self, phone):
        tmp_session = Crypto.random_tmp_session()

        self.session.data["tmp_session"] = tmp_session
        self.session.data["phone_number"] = phone
        self.session.save()

        result = await self.transport.send_handshake(
            "sendCode",
            {
                "phone_number": phone,
                "send_type": "SMS",
            },
        )

        response = result.get(
            "data",
            {},
        )

        if not isinstance(response, dict):
            return result

        data = response.get(
            "data",
            {},
        )

        if isinstance(data, dict):
            phone_code_hash = data.get(
                "phone_code_hash"
            )

            if phone_code_hash:
                self.session.data[
                    "phone_code_hash"
                ] = phone_code_hash
                self.session.save()

        return result

    async def sign_in(
        self,
        phone,
        phone_code,
        phone_code_hash=None,
    ):
        tmp_session = (
            self.session.tmp_session
        )

        if not tmp_session:
            raise AuthenticationError(
                "Temporary session not found."
            )

        phone_code_hash = (
            phone_code_hash
            or self.session.data.get(
                "phone_code_hash"
            )
        )

        if not phone_code_hash:
            raise AuthenticationError(
                "phone_code_hash not found."
            )

        public_key, private_key = (
            Crypto.generate_rsa_keypair()
        )

        result = await self.transport.send_handshake(
            "signIn",
            {
                "phone_number": phone,
                "phone_code_hash":
                    phone_code_hash,
                "phone_code": phone_code,
                "public_key": public_key,
            },
        )

        response = result.get(
            "data",
            {},
        )

        if not isinstance(response, dict):
            return result

        data = response.get(
            "data",
            {},
        )

        if not isinstance(data, dict):
            return result

        if data.get("status") not in (
            None,
            "OK",
        ):
            return result

        encrypted_auth = data.get(
            "auth"
        )

        if not encrypted_auth:
            raise AuthenticationError(
                "Authentication token not found."
            )

        try:
            auth = Crypto.decrypt_rsa_oaep(
                private_key,
                encrypted_auth,
            )
        except Exception as exc:
            raise AuthenticationError(
                "Could not decrypt authentication token."
            ) from exc

        user = data.get(
            "user",
            {},
        )

        user_guid = ""

        if isinstance(user, dict):
            user_guid = (
                user.get("user_guid")
                or ""
            )

        self.session.set_auth(
            auth=auth,
            private_key=private_key,
            phone=phone,
            user_guid=user_guid,
            public_key=public_key,
        )

        permanent_key = (
            Crypto.derive_session_key(auth)
        )

        self.session.set_key(
            permanent_key
        )

        self.session.set_iv(
            b"\x00" * 16
        )

        self.session.data.pop(
            "phone_code_hash",
            None,
        )

        self.session.save()

        return result