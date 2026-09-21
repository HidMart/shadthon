from __future__ import annotations

import json

import aiohttp

from .crypto import Crypto
from .exceptions import APIError, NetworkError


class Transport:
    def __init__(
        self,
        base_url,
        auth=None,
        private_key=None,
        timeout=30,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.private_key = private_key
        self.timeout = timeout

    def _authenticated_key(self):
        if not self.auth:
            raise APIError(
                "No authentication key available"
            )

        auth = str(self.auth)

        return Crypto.derive_session_key(auth)

    async def request(
        self,
        method,
        input_data=None,
        *,
        tmp_session=None,
        authenticated=False,
        client_info=None,
    ):
        client = client_info or {
            "app_name": "Main",
            "app_version": "4.4.26",
            "platform": "Web",
            "package": "web.shad.ir",
            "lang_code": "fa",
        }

        inner = {
            "client": client,
            "method": method,
            "input": input_data or {},
        }

        inner_json = json.dumps(
            inner,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        if authenticated:
            if not self.auth:
                raise APIError(
                    "No authentication key available"
                )

            auth_value = str(self.auth)

            key = self._authenticated_key()

        else:
            if not tmp_session:
                raise APIError(
                    "No temporary session available"
                )

            key = Crypto.derive_session_key(
                str(tmp_session)
            )

        data_enc = Crypto.encrypt_payload(
            key,
            inner_json.encode("utf-8"),
        )

        if authenticated:
            payload = {
                "api_version": "6",
                "auth": Crypto.decode_auth(
                    auth_value
                ),
                "data_enc": data_enc,
            }

            if self.private_key:
                payload["sign"] = Crypto.sign_rsa(
                    self.private_key,
                    data_enc,
                )
            else:
                payload["sign"] = Crypto.compute_sign(
                    key,
                    data_enc,
                )

        else:
            payload = {
                "api_version": "6",
                "tmp_session": str(
                    tmp_session
                ),
                "data_enc": data_enc,
            }

        try:
            timeout = aiohttp.ClientTimeout(
                total=self.timeout
            )

            async with aiohttp.ClientSession(
                timeout=timeout
            ) as session:

                async with session.post(
                    self.base_url + "/",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                    },
                ) as response:

                    text = await response.text()

                    try:
                        result = json.loads(text)

                    except json.JSONDecodeError:
                        raise APIError(
                            "Invalid JSON response: "
                            + text[:500]
                        )

                    if response.status >= 400:
                        raise APIError(
                            f"HTTP {response.status}: "
                            f"{result}"
                        )

                    return await self._decode_response(
                        result,
                        key,
                    )

        except aiohttp.ClientError as exc:
            raise NetworkError(
                str(exc)
            ) from exc

    async def send_authenticated(
        self,
        method,
        input_data=None,
        client_info=None,
    ):
        return await self.request(
            method,
            input_data,
            authenticated=True,
            client_info=client_info,
        )

    async def send_handshake(
        self,
        method,
        input_data=None,
        tmp_session=None,
        client_info=None,
    ):
        return await self.request(
            method,
            input_data,
            tmp_session=tmp_session,
            authenticated=False,
            client_info=client_info,
        )

    async def _decode_response(
        self,
        result,
        key,
    ):
        if not isinstance(result, dict):
            return result

        if "data_enc" not in result:
            return result

        encrypted = result["data_enc"]

        try:
            decrypted = Crypto.decrypt_payload(
                key,
                encrypted,
            )

            if isinstance(decrypted, bytes):
                decrypted = decrypted.decode(
                    "utf-8"
                )

            data = json.loads(decrypted)

            return {
                **result,
                "data": data,
            }

        except Exception as exc:
            raise APIError(
                f"Failed to decrypt response: {exc}"
            ) from exc

    async def close(self):
        return None