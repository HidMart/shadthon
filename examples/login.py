import asyncio

from shadthon import Client


async def main():
    phone = input(
        "Phone number: "
    ).strip()

    client = Client(phone)

    code_info = await client.send_code()

    print(
        "Verification code sent."
    )

    otp = input(
        "Enter verification code: "
    ).strip()

    result = await client.login(
        otp,
        code_info["phone_code_hash"],
    )

    print(
        "Login completed successfully."
    )

    if result.user:
        print(
            "User GUID:",
            result.user.guid,
        )
    else:
        print(
            "User GUID:",
            client.session.user_guid,
        )


if __name__ == "__main__":
    asyncio.run(main())