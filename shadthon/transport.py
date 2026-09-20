from __future__ import annotations

import json
import random
from typing import Any

import aiohttp

from .crypto import Crypto, CryptoError
from .exceptions import (
    NetworkError,
    ProtocolError,
)
from .session import Session


DC_ENDPOINT = (
    "https://shgetdcmess.iranlms.ir/"
)

DEFAULT_API_HOSTS = (
    "shadmessenger2.iranlms.ir",
)

DEFAULT_CLIENT = {
    "app_name": "Main",
    "app_version": "4.1.12",
    "platform": "Web",
    "package": "web.shad.ir",
    "lang_code": "fa",
}


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

    @staticmethod
    def client_info() -> dict[str, Any]:
        return dict(DEFAULT_CLIENT)

    def build_inner(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "method": method,
            "input": input_data,
            "client": self.client_info(),
        }

    async def _request_json(
        self,
        url: str,
        *,
        json_data: dict[str, Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:

        try:
            async with aiohttp.ClientSession(
                timeout=self.timeout
            ) as http:

                async with http.post(
                    url,
                    json=json_data,
                    data=data,
                    headers=headers,
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
                            "Invalid JSON response: "
                            + text[:500]
                        ) from exc

                    if not isinstance(
                        result,
                        dict,
                    ):
                        raise ProtocolError(
                            "Server response is not an object."
                        )

                    return result

        except aiohttp.ClientError as exc:
            raise NetworkError(
                str(exc)
            ) from exc

    async def refresh_dc_hosts(
        self,
    ) -> tuple[list[str], list[str]]:

        try:
            async with aiohttp.ClientSession(
                timeout=self.timeout
            ) as http:

                async with http.get(
                    DC_ENDPOINT
                ) as response:

                    text = await response.text()

                    if response.status >= 400:
                        raise NetworkError(
                            f"DC server returned "
                            f"HTTP {response.status}"
                        )

                    data = json.loads(text)

        except aiohttp.ClientError as exc:
            raise NetworkError(
                str(exc)
            ) from exc

        except json.JSONDecodeError as exc:
            raise ProtocolError(
                "Invalid DC server response."
            ) from exc

        api_hosts: list[str] = []
        websocket_hosts: list[str] = []

        root = data.get(
            "data",
            {},
        )

        if not isinstance(root, dict):
            root = {}

        api_data = root.get(
            "API",
            {},
        )

        socket_data = root.get(
            "socket",
            {},
        )

        if isinstance(
            api_data,
            dict,
        ):
            api_hosts = [
                str(value).strip()
                for value in api_data.values()
                if value
            ]

        if isinstance(
            socket_data,
            dict,
        ):
            websocket_hosts = [
                str(value).strip()
                for value in socket_data.values()
                if value
            ]

        api_hosts = [
            self._normalize_host(host)
            for host in api_hosts
        ]

        websocket_hosts = [
            self._normalize_ws_url(host)
            for host in websocket_hosts
        ]

        api_hosts = [
            host
            for host in api_hosts
            if host
        ]

        websocket_hosts = [
            host
            for host in websocket_hosts
            if host
        ]

        if not api_hosts:
            api_hosts = list(
                DEFAULT_API_HOSTS
            )

        self.session.api_hosts = api_hosts
        self.session.websocket_hosts = (
            websocket_hosts
        )

        if not self.session.messenger_host:
            self.session.messenger_host = (
                api_hosts[0]
            )

        return (
            api_hosts,
            websocket_hosts,
        )

    @staticmethod
    def _normalize_host(
        host: str,
    ) -> str:

        host = host.strip()

        host = host.removeprefix(
            "https://"
        )

        host = host.removeprefix(
            "http://"
        )

        host = host.rstrip("/")

        return host

    @staticmethod
    def _normalize_ws_url(
        host: str,
    ) -> str:

        host = host.strip()

        if host.startswith(
            "ws://"
        ) or host.startswith(
            "wss://"
        ):
            return host.rstrip("/")

        if host.startswith(
            "https://"
        ):
            return (
                "wss://"
                + host[8:].rstrip("/")
            )

        if host.startswith(
            "http://"
        ):
            return (
                "ws://"
                + host[7:].rstrip("/")
            )

        return (
            "wss://"
            + host.rstrip("/")
        )

    async def ensure_hosts(
        self,
    ) -> None:

        if (
            not self.session.api_hosts
            or not self.session.websocket_hosts
        ):
            await self.refresh_dc_hosts()

    @property
    def host(self) -> str:

        if self.session.messenger_host:
            return self.session.messenger_host

        if self.session.api_hosts:
            return random.choice(
                self.session.api_hosts
            )

        return DEFAULT_API_HOSTS[0]

    @property
    def url(self) -> str:
        return (
            "https://"
            + self.host
            + "/"
        )

    async def authenticated(
        self,
        method: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:

        if not self.session.auth:
            raise ProtocolError(
                "No Shad auth token is configured."
            )

        await self.ensure_hosts()

        crypto = Crypto(
            self.session.auth
        )

        inner = self.build_inner(
            method,
            input_data,
        )

        encoded = json.dumps(
            inner,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        encrypted = crypto.encrypt(
            encoded
        )

        payload = {
            "api_version": "5",
            "auth":
                self.session.auth,
            "data_enc":
                encrypted,
        }

        result = await self._request_json(
            self.url,
            json_data=payload,
            headers={
                "Content-Type":
                    "application/json",
                "Accept":
                    "application/json",
            },
        )

        return self.decode_response(
            result,
            crypto,
        )

    @staticmethod
    def decode_response(
        result: dict[str, Any],
        crypto: Crypto,
    ) -> dict[str, Any]:

        status = result.get(
            "status"
        )

        if (
            status
            and status != "OK"
        ):
            detail = result.get(
                "status_det"
            )

            raise ProtocolError(
                f"Shad error: "
                f"{status}"
                + (
                    f" ({detail})"
                    if detail
                    else ""
                )
            )

        encrypted = result.get(
            "data_enc"
        )

        if not encrypted:
            return result

        try:
            decoded = crypto.decrypt(
                encrypted
            )

            value = json.loads(
                decoded
            )

        except (
            CryptoError,
            json.JSONDecodeError,
        ) as exc:
            raise ProtocolError(
                "Unable to decrypt Shad v5 response."
            ) from exc

        if not isinstance(
            value,
            dict,
        ):
            raise ProtocolError(
                "Decrypted Shad response is not an object."
            )

        return value