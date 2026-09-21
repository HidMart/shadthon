import asyncio

from shadthon import Client


client = Client(
    session_name="my_account"
)


@client.on_message
async def handle_message(message):
    print(
        f"[{message.chat_guid}] "
        f"{message.author_guid}: "
        f"{message.text}"
    )

    if message.text.strip() == "سلام ربات":
        await message.reply(
            "روشن شد"
        )


async def main():
    print(
        "Shadthon 0.1.0"
    )
    print(
        "Waiting for messages..."
    )

    await client.start()


if __name__ == "__main__":
    asyncio.run(main())