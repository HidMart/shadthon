from __future__ import annotations

import json

import aiohttp

from .crypto import Crypto
from .exceptions import APIError, NetworkError


CLIENT_META = {
    "app_name": "Main",
    "app_version": "4.4.26",
    "platform": "Web",
    "package": "web.shad.ir",
    "lang_code": "fa",
}


class Transport:
    def __init__(
        self,
        session,
        timeout=30,
    ):
        self.session = session
        self.timeout = timeout

    async def _post(self, payload):
        body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        url = self.session.get_base_url()

        timeout = aiohttp.ClientTimeout(
            total=self.timeout
        )

        try:
            async with aiohttp.ClientSession(
                timeout=timeout
            ) as http:
                async with http.post(
                    url,
                    data=body,
                    headers={
                        "Content-Type":
                            "application/json",
                        "Accept":
                            "application/json",
                    },
                ) as response:

                    text = await response.text()

                    try:
                        result = json.loads(text)
                    except json.JSONDecodeError as exc:
                        raise APIError(
                            f"Invalid JSON response: "
                            f"{text[:500]}"
                        ) from exc

                    if response.status >= 400:
                        raise APIError(
                            f"HTTP {response.status}: "
                            f"{result}"
                        )

                    return result

        except aiohttp.ClientError as exc:
            raise NetworkError(
                str(exc)
            ) from exc

    def _build_inner(
        self,
        method,
        input_data,
    ):
        return json.dumps(
            {
                "client": CLIENT_META,
                "method": method,
                "input": input_data or {},
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

    async def send_authenticated(
        self,
        method,
        input_data=None,
    ):
        if not self.session.has_auth():
            raise APIError(
                "Authenticated session is not available."
            )

        raw = self._build_inner(
            method,
            input_data,
        )

        data_enc = Crypto.encrypt_payload(
            self.session.get_key(),
            raw,
            self.session.get_iv(),
        )

        auth = (
            self.session.decode_auth
            or Crypto.decode_auth(
                self.session.auth
            )
        )

        payload = {
            "api_version": "6",
            "auth": auth,
            "data_enc": data_enc,
        }

        if self.session.private_key:
            payload["sign"] = Crypto.sign_rsa(
                self.session.private_key,
                data_enc,
            )
        else:
            payload["sign"] = Crypto.compute_sign(
                self.session.get_key(),
                data_enc,
            )

        response = await self._post(
            payload
        )

        return await self._decode_response(
            response
        )

    async def send_handshake(
        self,
        method,
        input_data=None,
    ):
        if not self.session.tmp_session:
            raise APIError(
                "Temporary session is not available."
            )

        raw = self._build_inner(
            method,
            input_data,
        )

        key = Crypto.derive_session_key(
            self.session.tmp_session
        )

        data_enc = Crypto.encrypt_payload(
            key,
            raw,
            b"\x00" * 16,
        )

        payload = {
            "api_version": "6",
            "tmp_session":
                self.session.tmp_session,
            "data_enc": data_enc,
        }

        response = await self._post(
            payload
        )

        return await self._decode_response(
            response,
            handshake=True,
        )

    async def send_initial(
        self,
        method,
        input_data=None,
    ):
        if not self.session.tmp_session:
            raise APIError(
                "Temporary session is not available."
            )

        raw = self._build_inner(
            method,
            input_data,
        )

        key = Crypto.derive_session_key(
            self.session.tmp_session
        )

        data_enc = Crypto.encrypt_payload(
            key,
            raw,
        )

        response = await self._post(
            {
                "api_version": "6",
                "data_enc": data_enc,
            }
        )

        return await self._decode_response(
            response,
            handshake=True,
        )

    async def _decode_response(
        self,
        result,
        handshake=False,
    ):
        if not isinstance(result, dict):
            return result

        data_enc = result.get(
            "data_enc"
        )

        if not data_enc:
            return result

        try:
            if handshake:
                if not self.session.tmp_session:
                    return result

                key = Crypto.derive_session_key(
                    self.session.tmp_session
                )

                raw = Crypto.decrypt_payload(
                    key,
                    data_enc,
                    b"\x00" * 16,
                )

            else:
                raw = Crypto.decrypt_payload(
                    self.session.get_key(),
                    data_enc,
                    self.session.get_iv(),
                )

        except Exception:
            if (
                handshake
                and self.session.tmp_session
            ):
                raw, key, iv = (
                    Crypto.decrypt_payload_probe(
                        self.session.tmp_session,
                        data_enc,
                    )
                )

                self.session.set_key(key)
                self.session.set_iv(iv)
                self.session.save()

            else:
                return result

        try:
            decoded = json.loads(
                raw.decode("utf-8")
            )
        except Exception:
            return result

        return {
            **result,
            "data": decoded,
        }

    async def request(
        self,
        method,
        input_data=None,
        *,
        authenticated=True,
    ):
        if authenticated:
            return await self.send_authenticated(
                method,
                input_data,
            )

        return await self.send_handshake(
            method,
            input_data,
        )

    async def close(self):
        return None