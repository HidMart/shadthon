from __future__ import annotations

import re


class Filter:
    def __init__(self, func):
        self.func = func

    async def check(self, message):
        result = self.func(message)

        if hasattr(result, "__await__"):
            result = await result

        return bool(result)

    def __and__(self, other):
        return Filter(
            lambda message: (
                self.func(message)
                and other.func(message)
            )
        )

    def __or__(self, other):
        return Filter(
            lambda message: (
                self.func(message)
                or other.func(message)
            )
        )

    def __invert__(self):
        return Filter(
            lambda message: not self.func(message)
        )


def _value(message, name, default=None):
    if isinstance(message, dict):
        return message.get(name, default)

    return getattr(
        message,
        name,
        default,
    )


class Filters:
    @property
    def all(self):
        return Filter(lambda message: True)

    @property
    def text(self):
        return Filter(
            lambda message: bool(
                _value(message, "text")
            )
        )

    @property
    def private(self):
        return Filter(
            lambda message: (
                _value(message, "chat_type")
                == "private"
            )
        )

    @property
    def group(self):
        return Filter(
            lambda message: (
                _value(message, "chat_type")
                == "group"
            )
        )

    def media(self):
        return Filter(
            lambda message: bool(
                _value(message, "media")
                or _value(message, "file")
                or _value(message, "photo")
            )
        )

    def command(
        self,
        command,
        prefixes="/",
    ):
        if isinstance(prefixes, str):
            prefixes = tuple(prefixes)

        command = str(command).lstrip(
            "".join(prefixes)
        )

        def check(message):
            text = _value(
                message,
                "text",
                "",
            )

            if not isinstance(text, str):
                return False

            for prefix in prefixes:
                if text.startswith(
                    prefix + command
                ):
                    return True

            return False

        return Filter(check)

    def contains(self, value):
        return Filter(
            lambda message: (
                str(value)
                in str(
                    _value(
                        message,
                        "text",
                        "",
                    )
                )
            )
        )

    def startswith(self, value):
        return Filter(
            lambda message: str(
                _value(
                    message,
                    "text",
                    "",
                )
            ).startswith(value)
        )

    def regex(self, pattern):
        compiled = re.compile(pattern)

        return Filter(
            lambda message: bool(
                compiled.search(
                    str(
                        _value(
                            message,
                            "text",
                            "",
                        )
                    )
                )
            )
        )

    def create(self, func):
        return Filter(func)


filters = Filters()