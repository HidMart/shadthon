from __future__ import annotations

import asyncio
import logging
import time


logger = logging.getLogger(
    "shadthon.dispatcher"
)

POLL_INTERVAL = 1.5
ERROR_BACKOFF = 5.0
MAX_ERRORS = 10


class Dispatcher:
    def __init__(self, client):
        self.client = client
        self.handlers = []
        self.state = 0
        self.running = False
        self.task = None

        self._seen_messages = set()

    def register_handler(self, handler):
        self.handlers.append(handler)

    def start(self):
        if self.running:
            return

        self.running = True

        self.task = asyncio.create_task(
            self._polling_loop()
        )

    async def stop(self):
        self.running = False

        if self.task and not self.task.done():
            self.task.cancel()

            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def _polling_loop(self):
        self.state = (
            self.client.session.state
            or int(time.time()) - 150
        )

        errors = 0

        while self.running:
            try:
                result = await self.client.get_chats_updates(
                    self.state
                )

                errors = 0

                data = result.get(
                    "data",
                    result,
                )

                if not isinstance(data, dict):
                    await asyncio.sleep(
                        POLL_INTERVAL
                    )
                    continue

                new_state = int(
                    data.get("state")
                    or data.get("new_state")
                    or self.state
                )

                if new_state > self.state:
                    self.state = new_state
                    self.client.session.state = new_state
                    self.client.session.save()

                chats = data.get(
                    "chats",
                    [],
                )

                if isinstance(chats, list):
                    for chat in chats:
                        if not isinstance(
                            chat,
                            dict,
                        ):
                            continue

                        message = chat.get(
                            "last_message"
                        )

                        if message:
                            await self._dispatch(
                                message,
                                chat.get(
                                    "object_guid",
                                    "",
                                ),
                            )

                updates = data.get(
                    "message_updates",
                    [],
                )

                if isinstance(
                    updates,
                    list,
                ):
                    for item in updates:
                        if not isinstance(
                            item,
                            dict,
                        ):
                            continue

                        message = item.get(
                            "message"
                        )

                        if message:
                            await self._dispatch(
                                message,
                                item.get(
                                    "object_guid",
                                    "",
                                ),
                            )

                await asyncio.sleep(
                    POLL_INTERVAL
                )

            except asyncio.CancelledError:
                break

            except Exception as exc:
                errors += 1

                logger.error(
                    "Polling error %d/%d: %s",
                    errors,
                    MAX_ERRORS,
                    exc,
                )

                if errors >= MAX_ERRORS:
                    self.running = False
                    break

                await asyncio.sleep(
                    ERROR_BACKOFF
                )

    async def _dispatch(
        self,
        raw_message,
        object_guid="",
    ):
        if not isinstance(
            raw_message,
            dict,
        ):
            return

        raw_message = dict(
            raw_message
        )

        if object_guid:
            raw_message.setdefault(
                "object_guid",
                object_guid,
            )

        message = self.client.message_from_dict(
            raw_message
        )

        if not message.id:
            return

        unique_id = (
            message.chat_guid,
            message.id,
        )

        if unique_id in self._seen_messages:
            return

        self._seen_messages.add(
            unique_id
        )

        if len(self._seen_messages) > 5000:
            self._seen_messages = set(
                list(
                    self._seen_messages
                )[-2500:]
            )

        for handler in self.handlers:
            asyncio.create_task(
                self._safe_call(
                    handler,
                    message,
                )
            )

    async def _safe_call(
        self,
        handler,
        message,
    ):
        try:
            await handler(message)
        except Exception:
            logger.exception(
                "Message handler failed"
            )