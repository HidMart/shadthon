import json
import aiohttp

from .crypto import (
    aes_decrypt,
    aes_encrypt,
    calculate_signature,
    probe_decrypt,
    rsa_sign,
    decode_auth,
)


DEFAULT_HOSTS = [
    "shadmessenger60.iranlms.ir",
    "shadmessenger145.iranlms.ir",
    "shadmessenger40.iranlms.ir",
    "shadmessenger57.iranlms.ir",
    "shadmessenger23.iranlms.ir",
]


CLIENT_INFO = {
    "app_name": "Main",
    "app_version": "4.4.26",
    "platform": "Web",
    "package": "web.shad.ir",
    "lang_code": "fa",
}


class Transport:
    def __init__(self, session):
        self.session = session
        self.hosts = list(DEFAULT_HOSTS)

        if session.messenger_host in self.hosts:
            self.hosts.remove(session.messenger_host)

        self.hosts.insert(
            0,
            session.messenger_host
            or DEFAULT_HOSTS[0],
        )

    def _inner(self, method, input_data):
        return json.dumps(
            {
                "client": CLIENT_INFO,
                "method": method,
                "input": input_data,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def _temporary_envelope(self, encrypted):
        return {
            "api_version": "6",
            "tmp_session": self.session.temporary_session,
            "data_enc": encrypted,
        }

    def _authenticated_envelope(self, encrypted):
        auth = (
            self.session.decoded_auth
            or decode_auth(self.session.auth)
        )

        if self.session.private_key_pem:
            signature = rsa_sign(
                self.session.private_key_pem,
                encrypted,
            )
        else:
            signature = calculate_signature(
                self.session.get_key(),
                encrypted,
            )

        return {
            "api_version": "6",
            "auth": auth,
            "data_enc": encrypted,
            "sign": signature,
        }

    async def _post(self, payload):
        last_error = None

        headers = {
            "Content-Type": "application/json",
            "Origin": "https://web.shad.ir",
            "Referer": "https://web.shad.ir/",
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/153.0.0.0 Safari/537.36"
            ),
        }

        timeout = aiohttp.ClientTimeout(
            total=30
        )

        async with aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
        ) as http:

            for host in self.hosts:
                try:
                    async with http.post(
                        f"https://{host}/",
                        json=payload,
                    ) as response:

                        text = await response.text()

                        if response.status >= 500:
                            continue

                        if response.status != 200:
                            last_error = RuntimeError(
                                f"HTTP {response.status}: {text}"
                            )
                            continue

                        self.session.messenger_host = host

                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            return {
                                "raw": text
                            }

                except Exception as exc:
                    last_error = exc

        if last_error:
            raise last_error

        raise RuntimeError(
            "No Shad server is available."
        )

    async def send_handshake(
        self,
        method,
        input_data,
    ):
        if not self.session.temporary_session:
            raise RuntimeError(
                "Temporary session has not been initialized."
            )

        inner = self._inner(
            method,
            input_data,
        )

        encrypted = aes_encrypt(
            inner,
            self.session.get_key(),
            self.session.get_iv(),
        )

        payload = self._temporary_envelope(
            encrypted
        )

        response = await self._post(payload)

        return self._decrypt_response(
            response,
            temporary=True,
        )

    async def send_authenticated(
        self,
        method,
        input_data,
    ):
        inner = self._inner(
            method,
            input_data,
        )

        encrypted = aes_encrypt(
            inner,
            self.session.get_key(),
            self.session.get_iv(),
        )

        payload = self._authenticated_envelope(
            encrypted
        )

        response = await self._post(payload)

        return self._decrypt_response(
            response,
            temporary=False,
        )

    async def send_direct(
        self,
        method,
        input_data,
    ):
        outer = json.dumps(
            {
                "client": CLIENT_INFO,
                "auth": self.session.decoded_auth,
                "method": method,
                "input": input_data,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

        encrypted = aes_encrypt(
            outer,
            self.session.get_key(),
            self.session.get_iv(),
        )

        response = await self._post(
            {
                "data_enc": encrypted
            }
        )

        return self._decrypt_response(
            response,
            temporary=False,
        )

    def _decrypt_response(
        self,
        response,
        temporary=False,
    ):
        if not isinstance(response, dict):
            return response

        encrypted = response.get(
            "data_enc"
        )

        if not encrypted:
            return response

        if temporary:
            try:
                decrypted = aes_decrypt(
                    encrypted,
                    self.session.get_key(),
                    self.session.get_iv(),
                )

                return json.loads(decrypted)

            except Exception:
                decrypted, key, iv = probe_decrypt(
                    encrypted,
                    self.session.temporary_session,
                )

                self.session.set_key(key)
                self.session.set_iv(iv)

                return json.loads(decrypted)

        decrypted = aes_decrypt(
            encrypted,
            self.session.get_key(),
            self.session.get_iv(),
        )

        return json.loads(decrypted)