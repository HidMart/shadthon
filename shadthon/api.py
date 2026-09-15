import json

import httpx

from .exceptions import ShadAPIError


class ShadHTTP:

    def __init__(self, base_url, timeout=20):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.headers = {
            "Content-Type": "text/plain",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 15; Mobile) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/110.0.0.0 Mobile Safari/537.36"
            ),
            "Referer": "https://web.shad.ir/"
        }

    async def post(self, payload):
        body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":")
        )

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    content=body.encode("utf-8")
                )

        except httpx.HTTPError as e:
            raise ShadAPIError(
                f"Connection error: {e}"
            )

        if response.status_code != 200:
            raise ShadAPIError(
                f"HTTP {response.status_code}: {response.text}"
            )

        try:
            return response.json()

        except Exception:
            raise ShadAPIError(
                "Server returned invalid JSON"
            )