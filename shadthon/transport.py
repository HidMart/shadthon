from __future__ import annotations

import json
from typing import Any

import aiohttp

from .crypto import (
    aes_decrypt,
    aes_encrypt,
    derive_temporary_key,
    rsa_sign,
)
from .exceptions import (
    NetworkError,
    ProtocolError,
)
from .session import Session
from .utils import generate_session_id


DEFAULT_HOSTS = (
    "shadmessenger2.iranlms.ir",
    "shadmessenger60.iranlms.ir",
    "shadmessenger145.iranlms.ir",
    "shadmessenger40.iranlms.ir",
    "shadmessenger57.iranlms.ir",
)


class Transport:

    def __init__(
        self,
        session: Session,
        timeout: int = 30,
    ):
        self.session = session

        self.timeout = aiohttp.ClientTimeout(
            total=timeout
        )

    @property
    def host(self) -> str:
        return (
            self.session.messenger_host
            or DEFAULT_HOSTS[0]
        )

    @property
    def url(self) -> str:
        return f"https://{self.host}/"

    @staticmethod
    def client_info() -> dict[str, Any]:
        return {
            "app_name": "Main",
            "app_version": "4.4.26",
            "platform": "Web",
            "package": "web.shad.ir",
            "lang_code": "fa",
        }

    def build_payload(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "method": method,
            "input": input_data,
            "client": self.client_info(),
        }

    async def post(
        self,
        payload: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:

        request_headers = {
            "Content-Type":
                "application/json",
            "Accept":
                "application/json, text/plain, */*",
            "User-Agent":
                "Shadthon/0.2.0",
        }

        if headers:
            request_headers.update(
                headers
            )

        try:
            async with aiohttp.ClientSession(
                timeout=self.timeout
            ) as http:

                async with http.post(
                    self.url,
                    json=payload,
                    headers=request_headers,
                ) as response:

                    text = await response.text()

                    if response.status >= 400:
                        raise NetworkError(
                            f"HTTP {response.status}: "
                            f"{text[:500]}"
                        )

                    try:
                        result = json.loads(text)

                    except json.JSONDecodeError as exc:
                        raise ProtocolError(
                            "Server returned invalid JSON: "
                            f"{text[:500]}"
                        ) from exc

                    if not isinstance(
                        result,
                        dict,
                    ):
                        raise ProtocolError(
                            "Server response is not a JSON object."
                        )

                    return result

        except aiohttp.ClientError as exc:
            raise NetworkError(
                str(exc)
            ) from exc

    async def direct(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:

        return await self.post(
            self.build_payload(
                method,
                input_data,
            )
        )

    async def legacy(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:

        payload = {
            "api_version": "3",
            "method": method,
            "data": input_data,
        }

        return await self.post(
            payload,
            headers={
                "Origin":
                    "https://shadweb.iranlms.ir",
                "Referer":
                    "https://shadweb.iranlms.ir/",
            },
        )

    async def handshake(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:

        if not self.session.temporary_session:
            self.session.temporary_session = (
                generate_session_id()
            )

        temporary_session = (
            self.session.temporary_session
        )

        key = derive_temporary_key(
            temporary_session
        )

        inner = self.build_payload(
            method,
            input_data,
        )

        encrypted = aes_encrypt(
            json.dumps(
                inner,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            key,
        )

        payload = {
            "api_version": "6",
            "tmp_session":
                temporary_session,
            "data_enc":
                encrypted,
        }

        result = await self.post(
            payload
        )

        return self._decode_result(
            result,
            key,
        )

    async def authenticated(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:

        if not self.session.auth:
            raise ProtocolError(
                "No authenticated session."
            )

        key = self.session.get_key()

        if key is None:
            raise ProtocolError(
                "Session encryption key is missing."
            )

        inner = self.build_payload(
            method,
            input_data,
        )

        encrypted = aes_encrypt(
            json.dumps(
                inner,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            key,
            self.session.get_iv(),
        )

        signature = ""

        if self.session.private_key_pem:
            signature = rsa_sign(
                encrypted,
                self.session.private_key_pem,
            )

        payload = {
            "api_version": "6",
            "auth":
                self.session.auth,
            "data_enc":
                encrypted,
            "sign":
                signature,
        }

        result = await self.post(
            payload
        )

        return self._decode_result(
            result,
            key,
        )

    async def send_handshake(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        return await self.handshake(
            method,
            input_data,
        )

    async def send_authenticated(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        return await self.authenticated(
            method,
            input_data,
        )

    @staticmethod
    def _decode_result(
        result: dict[str, Any],
        key: bytes,
    ) -> dict[str, Any]:

        if "data_enc" not in result:
            return result

        try:
            decoded = aes_decrypt(
                result["data_enc"],
                key,
            )

            value = json.loads(
                decoded
            )

            if not isinstance(
                value,
                dict,
            ):
                raise ProtocolError(
                    "Decrypted response is not a JSON object."
                )

            return value

        except ProtocolError:
            raise

        except Exception as exc:
            raise ProtocolError(
                "Unable to decrypt server response."
            ) from exc