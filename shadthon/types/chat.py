from __future__ import annotations


class Chat:
    def __init__(
        self,
        client=None,
        guid=None,
        title=None,
        chat_type=None,
        username=None,
        description=None,
        members_count=None,
        raw=None,
        **kwargs,
    ):
        self.client = client
        self.guid = guid
        self.title = title
        self.type = chat_type
        self.username = username
        self.description = description
        self.members_count = members_count
        self.raw = raw if raw is not None else kwargs

    @classmethod
    def from_dict(cls, data, client=None):
        if not isinstance(data, dict):
            return cls(
                client=client,
                raw=data,
            )

        return cls(
            client=client,
            guid=data.get(
                "object_guid",
                data.get("guid"),
            ),
            title=data.get(
                "title",
                data.get("name"),
            ),
            chat_type=data.get(
                "type",
                data.get("chat_type"),
            ),
            username=data.get("username"),
            description=data.get("description"),
            members_count=data.get("members_count"),
            raw=data,
        )

    async def send_message(self, text):
        return await self.client.send_message(
            self.guid,
            text,
        )

    async def get_messages(self, limit=50):
        return await self.client.get_messages(
            self.guid,
            limit=limit,
        )

    async def get_chat_history(self, limit=50):
        return await self.client.get_chat_history(
            self.guid,
            limit=limit,
        )

    def __repr__(self):
        return (
            f"Chat("
            f"guid={self.guid!r}, "
            f"title={self.title!r}, "
            f"type={self.type!r}"
            f")"
        )