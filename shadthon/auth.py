from __future__ import annotations

import base64
import re

from Crypto.PublicKey import RSA

from .crypto import Crypto
from .exceptions import AuthenticationError


class AuthManager:
    def __init__(self, transport, session):
        self.transport = transport
        self.session = session

    def _find_value(self, data, *keys):
        if not isinstance(data, dict):
            return None

        for key in keys:
            if key in data:
                return data[key]

        for value in data.values():
            if isinstance(value, dict):
                found = self._find_value(value, *keys)

                if found is not None:
                    return found

        return None

    def _normalize_phone(self, phone):
        phone = str(phone).strip()

        digits = phone.translate(
            str.maketrans(
                "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
                "01234567890123456789",
            )
        )

        digits = re.sub(r"\D", "", digits)

        if digits.startswith("0098"):
            digits = digits[2:]

        if digits.startswith("09"):
            digits = "98" + digits[1:]

        elif digits.startswith("9") and len(digits) == 10:
            digits = "98" + digits

        elif digits.startswith("+98"):
            digits = digits[1:]

        if not digits.startswith("98") or len(digits) != 12:
            raise ValueError(
                "Invalid Iranian phone number. "
                "Use 989xxxxxxxxx or 09xxxxxxxxx."
            )

        return digits

    async def send_code(self, phone):
        phone = self._normalize_phone(phone)

        self.session.data["phone_number"] = phone

        tmp_session = Crypto.generate_tmp_session()

        self.session.tmp_session = tmp_session

        result = await self.transport.send_handshake(
            "sendCode",
            {
                "phone_number": phone,
                "send_type": "SMS",
            },
            tmp_session=tmp_session,
        )

        data = result.get("data", result)

        if not isinstance(data, dict):
            data = {}

        status = data.get("status")

        if status and status not in ("OK", "SUCCESS"):
            raise AuthenticationError(
                f"sendCode failed: {data}"
            )

        phone_code_hash = self._find_value(
            data,
            "phone_code_hash",
            "phoneCodeHash",
        )

        if phone_code_hash:
            self.session.data["phone_code_hash"] = phone_code_hash

        self.session.save()

        return result

    async def sign_in(
        self,
        phone,
        phone_code,
        phone_code_hash=None,
    ):
        phone = self._normalize_phone(phone)

        if not phone_code_hash:
            phone_code_hash = self.session.data.get(
                "phone_code_hash",
                "",
            )

        if not phone_code_hash:
            raise AuthenticationError(
                "phone_code_hash is missing."
            )

        tmp_session = self.session.tmp_session

        if not tmp_session:
            raise AuthenticationError(
                "Temporary session is missing. "
                "Send code again."
            )

        key = RSA.generate(1024)

        private_key = key.export_key().decode()

        public_key = key.publickey().export_key(
            format="DER"
        )

        public_key_b64 = base64.b64encode(
            public_key
        ).decode()

        self.session.data["private_key"] = private_key
        self.session.data["public_key"] = public_key_b64

        result = await self.transport.send_handshake(
            "signIn",
            {
                "phone_number": phone,
                "phone_code_hash": phone_code_hash,
                "phone_code": str(phone_code),
                "public_key": public_key_b64,
            },
            tmp_session=tmp_session,
        )

        data = result.get("data", result)

        if not isinstance(data, dict):
            data = {}

        status = data.get("status")

        if status and status not in ("OK", "SUCCESS"):
            raise AuthenticationError(
                f"signIn failed: {data}"
            )

        auth = self._find_value(
            data,
            "auth",
            "auth_token",
        )

        if not auth:
            raise AuthenticationError(
                "Login succeeded but auth was not returned: "
                f"{data}"
            )

        user_guid = self._find_value(
            data,
            "user_guid",
            "userGuid",
            "guid",
        )

        auth_value = auth

        try:
            decoded_auth = base64.b64decode(
                auth,
                validate=True,
            )
        except Exception:
            decoded_auth = auth.encode()

        decrypted_auth = None

        try:
            decrypted_auth = Crypto.decrypt_rsa(
                private_key,
                decoded_auth,
            )
        except Exception:
            try:
                decrypted_auth = Crypto.decrypt_rsa(
                    private_key,
                    auth,
                )
            except Exception:
                decrypted_auth = None

        if decrypted_auth:
            if isinstance(
                decrypted_auth,
                bytes,
            ):
                decrypted_auth = decrypted_auth.decode(
                    errors="ignore"
                )

            auth_value = decrypted_auth

        self.session.set_auth(
            auth_value,
            private_key,
            phone=phone,
            user_guid=user_guid,
            public_key=public_key_b64,
        )

        self.session.save()

        return result