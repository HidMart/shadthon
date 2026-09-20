import asyncio

from shadthon import Client


AUTH = "YOUR_SHAD_AUTH"


client = Client(
    auth=AUTH,
    session_name="my_account",
)


@client.on_message
async def handler(message):

    print(
        "MESSAGE:",
        message.text,
    )

    if (
        message.text
        and "سلام" in message.text
    ):

        if message.object_guid:

            await client.send_message(
                message.object_guid,
                "سلام خوبی؟",
                reply_to_message_id=(
                    message.message_id
                ),
            )


async def main():
    print(
        "Shadthon 0.3.0"
    )

    print(
        "Authenticated:",
        client.is_authenticated(),
    )

    await client.run()


if __name__ == "__main__":
    asyncio.run(main())