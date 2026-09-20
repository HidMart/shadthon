import random
import string


def generate_session_id(length: int = 32) -> str:
    alphabet = string.ascii_lowercase
    return "".join(random.choice(alphabet) for _ in range(length))


def normalize_phone(phone: str) -> str:
    value = str(phone).strip().replace(" ", "").replace("-", "")

    if value.startswith("+"):
        value = value[1:]

    if value.startswith("00"):
        value = value[2:]

    if value.startswith("98") and len(value) >= 12:
        return value

    if value.startswith("0") and len(value) == 11:
        return "98" + value[1:]

    if len(value) == 10 and value.startswith("9"):
        return "98" + value

    return value


def split_phone(phone: str):
    full = normalize_phone(phone)

    if full.startswith("98"):
        return full[2:], "98"

    return full, "98"