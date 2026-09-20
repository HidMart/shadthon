from .crypto import Crypto
from .exceptions import AuthenticationError


class AuthManager:
    def __init__(
        self,
        transport,
        session,
    ):
        self.transport = transport
        self.session = session

    async def send_code(
        self,
        phone,
    ):
        tmp_session = Crypto.random_tmp_session()

        result = await self.transport.request(
            "sendCode",
            {
                "phone_number": phone,
                "send_type": "SMS",
            },
            tmp_session=tmp_session,
            authenticated=False,
        )

        if result.get("status") != "OK":
            return result

        data = result.get(
            "data",
            {},
        )

        self.session.data[
            "tmp_session"
        ] = tmp_session

        self.session.data[
            "phone"
        ] = phone

        self.session.data[
            "phone_code_hash"
        ] = data.get(
            "phone_code_hash"
        )

        self.session.save()

        return result

    async def sign_in(
        self,
        phone,
        phone_code,
        phone_code_hash=None,
    ):
        tmp_session = self.session.data.get(
            "tmp_session"
        )

        if not tmp_session:
            raise AuthenticationError(
                "Temporary session not found"
            )

        if not phone_code_hash:
            phone_code_hash = self.session.data.get(
                "phone_code_hash"
            )

        if not phone_code_hash:
            raise AuthenticationError(
                "phone_code_hash not found"
            )

        public_key, private_key = (
            Crypto.generate_rsa_keypair()
        )

        result = await self.transport.request(
            "signIn",
            {
                "phone_number": phone,
                "phone_code_hash": phone_code_hash,
                "phone_code": phone_code,
                "public_key": public_key,
            },
            tmp_session=tmp_session,
            authenticated=False,
        )

        if result.get("status") != "OK":
            return result

        data = result.get(
            "data",
            {},
        )

        encrypted_auth = data.get(
            "auth"
        )

        if not encrypted_auth:
            raise AuthenticationError(
                "Authentication token not found"
            )

        try:
            auth = Crypto.decrypt_rsa_oaep(
                private_key,
                encrypted_auth,
            )
        except Exception as exc:
            raise AuthenticationError(
                "Could not decrypt authentication token"
            ) from exc

        self.session.set_auth(
            auth=auth,
            private_key=private_key,
            phone=phone,
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