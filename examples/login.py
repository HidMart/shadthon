import asyncio

from shadthon import Client


async def main():
    phone = input("Phone number: ").strip()

    if phone.startswith("09"):
        phone = "98" + phone[1:]
    elif phone.startswith("+98"):
        phone = phone[1:]

    print(f"Using: {phone}")

    client = Client(
        phone=phone,
        session_name="my_account",
    )

    print("\nsendCode:")

    result = await client.send_code(
        phone
    )

    print(result)

    if result.get("status") != "OK":
        print("sendCode failed")
        return

    print(
        "\nکد ورود را از داخل شاد دریافت کن."
    )

    code = input(
        "Login code: "
    ).strip()

    print("\nsignIn:")

    result = await client.sign_in(
        phone=phone,
        phone_code=code,
    )

    print(result)

    if result.get("status") == "OK":
        print(
            "\nLogin successful"
        )
        print(
            "Session saved."
        )
    else:
        print(
            "\nLogin failed"
        )


if __name__ == "__main__":
    asyncio.run(main())