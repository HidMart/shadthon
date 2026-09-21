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
    client = Client(
        session_name="my_account"
    )

    if client.authenticated:
        print(
            "Session already authenticated."
        )
        return client

    phone = normalize_phone(
        input(
            "شماره شاد را وارد کن: "
        )
    )

    print(
        "در حال ارسال کد..."
    )

    result = await client.send_code(
        phone
    )

    response = result.get(
        "data",
        {},
    )

    data = (
        response.get("data", {})
        if isinstance(response, dict)
        else {}
    )

    phone_code_hash = data.get(
        "phone_code_hash"
    )

    if not phone_code_hash:
        print(
            "خطا در دریافت phone_code_hash"
        )
        print(result)
        return client

    print(
        "کد ارسال شد."
    )

    code = input(
        "کد ورود: "
    ).strip()

    result = await client.sign_in(
        phone=phone,
        phone_code=code,
        phone_code_hash=phone_code_hash,
    )

    print(
        "ورود انجام شد."
    )

    return client


if __name__ == "__main__":
    asyncio.run(main())