class User:
    def __init__(
        self,
        user_id=None,
        username=None,
        first_name=None,
        last_name=None,
        phone=None,
        raw=None,
    ):
        self.id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.raw = raw or {}

    def __repr__(self):
        return (
            f"User(id={self.id!r}, "
            f"username={self.username!r})"
        )


class Chat:
    def __init__(
        self,
        chat_id=None,
        title=None,
        chat_type=None,
        raw=None,
    ):
        self.id = chat_id
        self.title = title
        self.type = chat_type
        self.raw = raw or {}

    def __repr__(self):
        return (
            f"Chat(id={self.id!r}, "
            f"title={self.title!r})"
        )


class Message:
    def __init__(
        self,
        client,
        message_id=None,
        text="",
        object_guid=None,
        author_guid=None,
        chat_id=None,
        raw=None,
    ):
        self.client = client
        self.id = message_id
        self.text = text or ""
        self.object_guid = object_guid
        self.author_guid = author_guid
        self.chat_id = chat_id
        self.raw = raw or {}

    async def reply(self, text):
        target = (
            self.object_guid
            or self.chat_id
            or self.author_guid
        )

        if not target:
            raise ValueError(
                "Message does not contain a destination"
            )

        return await self.client.send_message(
            target,
            text,
        )

    async def answer(self, text):
        return await self.reply(text)

    def __repr__(self):
        return (
            f"Message(id={self.id!r}, "
            f"text={self.text!r}, "
            f"object_guid={self.object_guid!r})"
        )