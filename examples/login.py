import asyncio

from shadthon import Client


async def main():
    client = Client(
        session_name="my_account"
    )

    if not client.authenticated:
        phone = input(
            "Phone number: "
        ).strip()

        result = await client.login(
            phone
        )

        print("SendCode result:")
        print(result)

        code = input(
            "SMS code: "
        ).strip()

        result = await client.verify(
            code
        )

        print("Login result:")
        print(result)

    print(
        "Authenticated:",
        client.authenticated
    )

    await client.run()


asyncio.run(main())