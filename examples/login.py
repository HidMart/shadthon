import asyncio

from shadthon import Shad


async def main():

    shad = Shad()

    phone = input(
        "شماره موبایل: "
    )

    try:

        await shad.login(phone)

    except Exception as e:

        print()
        print("Shadthon:")
        print(e)


asyncio.run(main())