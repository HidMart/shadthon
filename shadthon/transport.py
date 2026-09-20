from __future__ import annotations

import json
from typing import Any

import aiohttp

from .crypto import (
    aes_decrypt,
    aes_encrypt,
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
    ) -> dict[str, Any]:
        headers = {
            "Content-Type":
                "application/json",
            "Accept":
                "application/json, text/plain, */*",
            "User-Agent":
                "Mozilla/5.0 Shadthon/0.2",
        }

        try:
            async with aiohttp.ClientSession(
                timeout=self.timeout
            ) as http:

                async with http.post(
                    self.url,
                    json=payload,
                    headers=headers,
                ) as response:

                    text = await response.text()

                    if response.status >= 400:
                        raise NetworkError(
                            f"HTTP {response.status}: {text[:500]}"
                        )

                    try:
                        return json.loads(text)
                    except json.JSONDecodeError as exc:
                        raise ProtocolError(
                            f"Invalid JSON response: {text[:500]}"
                        ) from exc

        except aiohttp.ClientError as exc:
            raise NetworkError(
                str(exc)
            ) from exc

    async def direct(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:

        payload = self.build_payload(
            method,
            input_data,
        )

        return await self.post(payload)

    async def handshake(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:

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
            self._temporary_key(),
        )

        payload = {
            "api_version": "6",
            "tmp_session": (
                self.session.temporary_session
                or generate_session_id()
            ),
            "data_enc": encrypted,
        }

        result = await self.post(payload)

        return self._decode_result(
            result,
            self._temporary_key(),
        )

    async def authenticated(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:

        if not self.session.auth:
            raise ProtocolError(
                "No authenticated session"
            )

        key = self._session_key()

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

        sign = ""

        if self.session.private_key_pem:
            sign = rsa_sign(
                encrypted,
                self.session.private_key_pem,
            )

        payload = {
            "api_version": "6",
            "auth": self.session.auth,
            "data_enc": encrypted,
            "sign": sign,
        }

        result = await self.post(payload)

        return self._decode_result(
            result,
            key,
        )

    def _temporary_key(self) -> bytes:
        return b"\x00" * 32

    def _session_key(self) -> bytes:
        if not self.session.key_hex:
            raise ProtocolError(
                "Session encryption key is missing"
            )

        try:
            return bytes.fromhex(
                self.session.key_hex
            )
        except ValueError as exc:
            raise ProtocolError(
                "Invalid session key"
            ) from exc

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

            return json.loads(decoded)

        except Exception:
            return result