from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator

import websockets
from websockets.exceptions import ConnectionClosed

from .crypto import Crypto
from .exceptions import NetworkError
from .session import Session
from .transport import Transport


class ShadWebSocket:

    def __init__(
        self,
        session: Session,
        transport: Transport,
        reconnect_delay: float = 3.0,
    ):
        self.session = session
        self.transport = transport
        self.reconnect_delay = (
            reconnect_delay
        )

        self._running = False

    async def _handshake(
        self,
        websocket: Any,
    ) -> None:

        payload = {
            "api_version": "5",
            "auth": self.session.auth,
            "data": "",
            "method": "handShake",
        }

        await websocket.send(
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )

    async def _heartbeat(
        self,
        websocket: Any,
    ) -> None:

        while self._running:

            try:
                await asyncio.sleep(
                    30
                )

                await websocket.send(
                    "0"
                )

            except Exception:
                return

    async def connect_once(
        self,
    ) -> AsyncIterator[dict[str, Any]]:

        if not self.session.auth:
            raise NetworkError(
                "Shad auth is required for WebSocket."
            )

        await self.transport.ensure_hosts()

        hosts = list(
            self.session.websocket_hosts
        )

        if not hosts:
            raise NetworkError(
                "No Shad WebSocket hosts were found."
            )

        crypto = Crypto(
            self.session.auth
        )

        for websocket_url in hosts:

            try:
                async with websockets.connect(
                    websocket_url,
                    ping_interval=None,
                    close_timeout=10,
                ) as websocket:

                    await self._handshake(
                        websocket
                    )

                    self._running = True

                    heartbeat_task = (
                        asyncio.create_task(
                            self._heartbeat(
                                websocket
                            )
                        )
                    )

                    try:
                        while self._running:

                            raw = (
                                await websocket.recv()
                            )

                            if isinstance(
                                raw,
                                bytes,
                            ):
                                raw = raw.decode(
                                    "utf-8",
                                    errors="ignore",
                                )

                            if raw == (
                                '{"status":"OK","status_det":"OK"}'
                            ):
                                continue

                            try:
                                message = json.loads(
                                    raw
                                )
                            except json.JSONDecodeError:
                                continue

                            if not isinstance(
                                message,
                                dict,
                            ):
                                continue

                            if (
                                message.get("type")
                                != "messenger"
                            ):
                                continue

                            encrypted = (
                                message.get(
                                    "data_enc"
                                )
                            )

                            if not encrypted:
                                continue

                            try:
                                decoded = (
                                    crypto.decrypt(
                                        encrypted
                                    )
                                )

                                data = json.loads(
                                    decoded
                                )

                            except Exception:
                                continue

                            if not isinstance(
                                data,
                                dict,
                            ):
                                continue

                            yield data

                    finally:
                        self._running = False
                        heartbeat_task.cancel()

                        try:
                            await heartbeat_task
                        except (
                            asyncio.CancelledError
                        ):
                            pass

            except (
                ConnectionClosed,
                OSError,
                asyncio.TimeoutError,
            ):
                self._running = False
                continue

        await asyncio.sleep(
            self.reconnect_delay
        )

    async def updates(
        self,
        *,
        message_updates: bool = True,
        chat_updates: bool = False,
        show_notifications: bool = False,
    ) -> AsyncIterator[dict[str, Any]]:

        while True:

            try:
                async for data in self.connect_once():

                    if (
                        message_updates
                        and "message_updates" in data
                    ):
                        updates = data.get(
                            "message_updates",
                            [],
                        )

                        if isinstance(
                            updates,
                            list,
                        ):
                            for item in updates:
                                if isinstance(
                                    item,
                                    dict,
                                ):
                                    yield item

                    if (
                        chat_updates
                        and "chat_updates" in data
                    ):
                        updates = data.get(
                            "chat_updates",
                            [],
                        )

                        if isinstance(
                            updates,
                            list,
                        ):
                            for item in updates:
                                if isinstance(
                                    item,
                                    dict,
                                ):
                                    yield item

                    if (
                        show_notifications
                        and "show_notifications"
                        in data
                    ):
                        updates = data.get(
                            "show_notifications",
                            [],
                        )

                        if isinstance(
                            updates,
                            list,
                        ):
                            for item in updates:
                                if isinstance(
                                    item,
                                    dict,
                                ):
                                    yield item

            except Exception:
                self._running = False

            await asyncio.sleep(
                self.reconnect_delay
            )

    async def close(self) -> None:
        self._running = False