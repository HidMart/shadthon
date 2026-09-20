import json
import aiohttp

from .crypto import encrypt, decrypt, auth_set, sign_rsa


DEFAULT_BASE_URL = "https://shadmessenger36.iranlms.ir/"


class Transport:
    def __init__(
        self,
        auth=None,
        private_key=None,
        tmp_session=None,
        base_url=DEFAULT_BASE_URL
    ):
        self.auth = auth
        self.private_key = private_key
        self.tmp_session = tmp_session
        self.base_url = (
            base_url or DEFAULT_BASE_URL
        ).rstrip("/") + "/"

    async def request(
        self,
        method,
        input_data=None,
        authenticated=False
    ):
        input_data = input_data or {}

        inner = {
            "method": method,
            "input": input_data,
            "client": {
                "app_name": "Main",
                "app_version": "4.4.26",
                "platform": "Web",
                "package": "web.shad.ir",
                "lang_code": "fa"
            }
        }

        if authenticated:
            crypto_auth = self.auth

            if not crypto_auth:
                raise RuntimeError(
                    "Authentication required"
                )
        else:
            crypto_auth = self.tmp_session

            if not crypto_auth:
                raise RuntimeError(
                    "tmp_session is missing"
                )

        encoded_inner = json.dumps(
            inner,
            ensure_ascii=False,
            separators=(",", ":")
        )

        data_enc = encrypt(
            crypto_auth,
            encoded_inner
        )

        outer = {
            "api_version": "6",
            "data_enc": data_enc
        }

        if authenticated:
            outer["auth"] = auth_set(
                self.auth
            )

            if self.private_key:
                outer["sign"] = sign_rsa(
                    self.private_key,
                    data_enc
                )
        else:
            outer["tmp_session"] = (
                self.tmp_session
            )

        timeout = aiohttp.ClientTimeout(
            total=30
        )

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.post(
                self.base_url,
                json=outer
            ) as response:

                response_text = await response.text()

                if response.status != 200:
                    raise RuntimeError(
                        f"HTTP {response.status}: "
                        f"{response_text}"
                    )

                try:
                    result = json.loads(
                        response_text
                    )
                except json.JSONDecodeError:
                    raise RuntimeError(
                        "Invalid JSON response: "
                        + response_text
                    )

        encrypted_response = result.get(
            "data_enc"
        )

        if encrypted_response:
            try:
                decrypted = decrypt(
                    crypto_auth,
                    encrypted_response
                )

                parsed = json.loads(
                    decrypted
                )

                return parsed

            except Exception as error:
                raise RuntimeError(
                    "Could not decrypt Shad response: "
                    + str(error)
                ) from error

        if result.get("status") != "OK":
            return result

        data = result.get("data")

        if isinstance(data, dict):
            return data

        return result

    async def close(self):
        return None