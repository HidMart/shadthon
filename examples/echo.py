from shadthon import Client


client = Client(
    session_name="my_account",
    socket_url="wss://shsocket14.iranlms.ir:80",
)


@client.on_message
async def message_handler(message):
    print(
        "MESSAGE:",
        message.text,
    )

    print(
        "GUID:",
        message.object_guid,
    )

    await message.reply(
        "سلام"
    )


client.run()