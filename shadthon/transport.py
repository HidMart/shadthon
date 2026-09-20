import json
import aiohttp

from .crypto import encrypt, decrypt, auth_set, sign_rsa


DEFAULT_DC = (
    "https://shadmessenger36.iranlms.ir/"
)


class Transport:
    def __init__(
        self,
        auth=None,
        private_key=None,
        tmp_session=None,
        base_url=DEFAULT_DC
    ):
        self.auth = auth
        self.private_key = private_key
        self.tmp_session = tmp_session
        self.base_url = base_url.rstrip("/") + "/"

    async def close(self):
        return None

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
            if not self.auth:
                raise RuntimeError(
                    "Authentication required"
                )

            crypto_auth = self.auth
        else:
            crypto_auth = self.tmp_session

        if not crypto_auth:
            raise RuntimeError(
                "No encryption session available"
            )

        data_enc = encrypt(
            crypto_auth,
            json.dumps(
                inner,
                ensure_ascii=False,
                separators=(",", ":")
            )
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

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                json=outer
            ) as response:

                response.raise_for_status()

                result = await response.json()

        if result.get("status") != "OK":
            return result

        encrypted_response = result.get(
            "data_enc"
        )

        if encrypted_response:
            try:
                decrypted = decrypt(
                    crypto_auth,
                    encrypted_response
                )

                return json.loads(decrypted)

            except Exception:
                return result

        if "data" in result:
            return result["data"]

        return result