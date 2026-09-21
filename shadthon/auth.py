from .crypto import Crypto
from .exceptions import AuthenticationError


class AuthManager:
    def __init__(self, transport, session):
        self.transport = transport
        self.session = session

    @staticmethod
    def _find_value(data, key):
        if not isinstance(data, dict):
            return None

        if key in data:
            return data[key]

        nested = data.get("data")

        if isinstance(nested, dict):
            value = AuthManager._find_value(
                nested,
                key,
            )

            if value is not None:
                return value

        return None

    async def send_code(self, phone):
        tmp_session = Crypto.random_tmp_session()

        self.session.tmp_session = tmp_session
        self.session.data["phone_number"] = phone

        self.session.save()

        result = await self.transport.send_handshake(
            "sendCode",
            {
                "phone_number": phone,
                "send_type": "SMS",
            },
        )

        phone_code_hash = self._find_value(
            result,
            "phone_code_hash",
        )

        if phone_code_hash:
            self.session.data[
                "phone_code_hash"
            ] = phone_code_hash

            self.session.save()

        status = self._find_value(
            result,
            "status",
        )

        if status not in (None, "OK"):
            raise AuthenticationError(
                f"sendCode failed: {result}"
            )

        return result

    async def sign_in(
        self,
        phone,
        phone_code,
        phone_code_hash=None,
    ):
        tmp_session = self.session.tmp_session

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

        self.session.data[
            "public_key"
        ] = public_key

        self.session.save()

        result = await self.transport.send_handshake(
            "signIn",
            {
                "phone_number": phone,
                "phone_code_hash": phone_code_hash,
                "phone_code": phone_code,
                "public_key": public_key,
            },
        )

        encrypted_auth = self._find_value(
            result,
            "auth",
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

        user = self._find_value(
            result,
            "user",
        )

        user_guid = ""

        if isinstance(user, dict):
            user_guid = (
                user.get("user_guid")
                or user.get("guid")
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
            "tmp_session",
            None,
        )

        self.session.data.pop(
            "phone_code_hash",
            None,
        )

        self.session.save()

        return result