import asyncio

from shadthon import Client


def normalize_phone(phone):
    phone = phone.strip()

    if phone.startswith("09"):
        return "98" + phone[1:]

    if phone.startswith("+98"):
        return phone[1:]

    return phone


async def main():
    phone = normalize_phone(
        input("Phone number: ")
    )

    print(f"Using: {phone}")

    client = Client(
        phone=phone,
        session_name="my_account",
    )

    print("\nsendCode:")

    result = await client.send_code(phone)

    print(result)

    response = result.get(
        "data",
        {},
    )

    if not isinstance(response, dict):
        print("Invalid sendCode response")
        return

    if response.get("status") != "OK":
        print("sendCode failed")
        return

    code_data = response.get(
        "data",
        {},
    )

    if not isinstance(code_data, dict):
        print("Invalid sendCode data")
        return

    phone_code_hash = code_data.get(
        "phone_code_hash"
    )

    if not phone_code_hash:
        print("phone_code_hash not found")
        return

    print(
        "\nکد ورود را از داخل شاد دریافت کن."
    )

    code = input(
        "Login code: "
    ).strip()

    if not code:
        print("Login code is required")
        return

    print("\nsignIn:")

    result = await client.sign_in(
        phone=phone,
        phone_code=code,
        phone_code_hash=phone_code_hash,
    )

    print(result)

    response = result.get(
        "data",
        {},
    )

    if (
        isinstance(response, dict)
        and response.get("status") == "OK"
    ):
        login_data = response.get(
            "data",
            {},
        )

        if (
            isinstance(login_data, dict)
            and login_data.get("status") == "OK"
        ):
            print("\nLogin successful")
            print("Session saved.")
            return

    print("\nLogin failed")


if __name__ == "__main__":
    asyncio.run(main())