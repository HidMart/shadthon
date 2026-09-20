import asyncio
import json

import aiohttp

from .crypto import Crypto


class ShadWebSocket:
    def __init__(
        self,
        url,
        auth,
        on_event=None,
    ):
        self.url = url
        self.auth = auth
        self.on_event = on_event

        self.websocket = None
        self.running = False

    async def connect(self):
        session = aiohttp.ClientSession()

        self._session = session

        self.websocket = await session.ws_connect(
            self.url,
            heartbeat=30,
        )

        await self.websocket.send_str(
            json.dumps(
                {
                    "api_version": "6",
                    "auth": self.auth,
                    "method": "handShake",
                },
                separators=(",", ":"),
            )
        )

        self.running = True

    async def run(self):
        if not self.websocket:
            await self.connect()

        while self.running:
            message = await self.websocket.receive()

            if message.type == aiohttp.WSMsgType.TEXT:
                await self._handle_text(
                    message.data
                )

            elif message.type in (
                aiohttp.WSMsgType.CLOSED,
                aiohttp.WSMsgType.CLOSE,
                aiohttp.WSMsgType.ERROR,
            ):
                self.running = False
                break

    async def _handle_text(self, text):
        if text == "0":
            return

        try:
            data = json.loads(text)
        except Exception:
            return

        if self.on_event:
            await self.on_event(data)

    async def close(self):
        self.running = False

        if self.websocket:
            await self.websocket.close()

        if hasattr(self, "_session"):
            await self._session.close()