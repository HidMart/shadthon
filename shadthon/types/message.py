from __future__ import annotations


class Message:
    def __init__(
        self,
        client=None,
        message_id=None,
        object_guid=None,
        text="",
        author_guid=None,
        chat_guid=None,
        chat_type=None,
        media=None,
        raw=None,
        reply_to_message_id=None,
        **kwargs,
    ):
        self.client = client
        self.id = message_id
        self.message_id = message_id
        self.object_guid = object_guid
        self.text = text or ""
        self.author_guid = author_guid
        self.chat_guid = chat_guid or object_guid
        self.chat_type = chat_type
        self.media = media
        self.raw = raw or kwargs
        self.reply_to_message_id = (
            reply_to_message_id
        )

    @classmethod
    def from_dict(
        cls,
        data,
        client=None,
    ):
        if not isinstance(data, dict):
            return cls(
                client=client,
                raw=data,
            )

        return cls(
            client=client,
            message_id=data.get(
                "message_id",
                data.get("messageId"),
            ),
            object_guid=data.get(
                "object_guid",
                data.get("objectGuid"),
            ),
            text=data.get(
                "text",
                "",
            ),
            author_guid=data.get(
                "author_guid",
                data.get("authorGuid"),
            ),
            chat_guid=data.get(
                "chat_guid",
                data.get("chatGuid"),
            ),
            chat_type=data.get(
                "chat_type",
                data.get("chatType"),
            ),
            media=data.get("media"),
            reply_to_message_id=data.get(
                "reply_to_message_id",
                data.get("replyToMessageId"),
            ),
            raw=data,
        )

    async def reply(
        self,
        text,
    ):
        return await self.client.send_message(
            self.object_guid,
            text,
            reply_to_message_id=self.id,
        )

    async def edit(
        self,
        text,
    ):
        return await self.client.edit_message(
            self.object_guid,
            self.id,
            text,
        )

    async def delete(self):
        return await self.client.delete_message(
            self.object_guid,
            self.id,
        )

    async def reply_photo(
        self,
        photo,
        caption="",
    ):
        return await self.client.send_photo(
            self.object_guid,
            photo,
            caption=caption,
            reply_to_message_id=self.id,
        )

    async def reply_file(
        self,
        file,
        caption="",
    ):
        return await self.client.send_file(
            self.object_guid,
            file,
            caption=caption,
            reply_to_message_id=self.id,
        )