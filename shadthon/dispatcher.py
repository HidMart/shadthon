from __future__ import annotations

import inspect


class Handler:
    def __init__(self, callback, filter_=None):
        self.callback = callback
        self.filter = filter_

    async def matches(self, message):
        if self.filter is None:
            return True

        return await self.filter.check(message)

    async def call(self, message):
        result = self.callback(message)

        if inspect.isawaitable(result):
            return await result

        return result


class Dispatcher:
    def __init__(self):
        self.handlers = []

    def add_handler(self, callback, filter_=None):
        handler = Handler(
            callback,
            filter_,
        )

        self.handlers.append(handler)

        return callback

    def remove_handler(self, callback):
        self.handlers = [
            handler
            for handler in self.handlers
            if handler.callback != callback
        ]

    async def dispatch(self, message):
        for handler in list(self.handlers):
            try:
                if await handler.matches(message):
                    await handler.call(message)
            except Exception:
                continue