import base64
import secrets
import string
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Util.Padding import pad, unpad


IV = b"\x00" * 16


def auth_set(value: str) -> str:
    result = []

    for char in value:
        if "a" <= char <= "z":
            result.append(chr(((32 - (ord(char) - 97)) % 26) + 97))
        elif "A" <= char <= "Z":
            result.append(chr(((29 - (ord(char) - 65)) % 26) + 65))
        elif "0" <= char <= "9":
            result.append(chr(((13 - (ord(char) - 48)) % 10) + 48))
        else:
            result.append(char)

    return "".join(result)


def make_key(auth: str) -> str:
    if len(auth) < 32:
        raise ValueError("auth must contain at least 32 characters")

    value = (
        auth[16:24]
        + auth[0:8]
        + auth[24:32]
        + auth[8:16]
    )

    result = []

    for char in value:
        if "0" <= char <= "9":
            result.append(chr(((ord(char) - 48 + 5) % 10) + 48))
        elif "a" <= char <= "z":
            result.append(chr(((ord(char) - 97 + 9) % 26) + 97))
        else:
            result.append(char)

    return "".join(result)


def encrypt(auth: str, data: str) -> str:
    key = make_key(auth).encode("utf-8")

    cipher = AES.new(
        key,
        AES.MODE_CBC,
        IV
    )

    encrypted = cipher.encrypt(
        pad(data.encode("utf-8"), AES.block_size)
    )

    return base64.b64encode(encrypted).decode("utf-8")


def decrypt(auth: str, data: str) -> str:
    key = make_key(auth).encode("utf-8")

    cipher = AES.new(
        key,
        AES.MODE_CBC,
        IV
    )

    decoded = base64.b64decode(data)

    decrypted = cipher.decrypt(decoded)

    return unpad(
        decrypted,
        AES.block_size
    ).decode("utf-8")


def generate_tmp_session() -> str:
    alphabet = string.ascii_lowercase
    return "".join(
        secrets.choice(alphabet)
        for _ in range(32)
    )


def generate_rsa_keys():
    key = RSA.generate(1024)

    private_key = key.export_key(
        format="DER",
        pkcs=8
    )

    public_key = key.publickey().export_key(
        format="DER"
    )

    public_b64 = base64.b64encode(
        public_key
    ).decode("utf-8")

    pem = (
        "-----BEGIN PUBLIC KEY-----\r\n"
        + public_b64
        + "\r\n-----END PUBLIC KEY-----"
    )

    pem_b64 = base64.b64encode(
        pem.encode("utf-8")
    ).decode("utf-8")

    public_value = auth_set(pem_b64)

    private_value = base64.b64encode(
        private_key
    ).decode("utf-8")

    return public_value, private_value


def load_private_key(private_key: str):
    raw = base64.b64decode(private_key)

    return RSA.import_key(raw)


def sign_rsa(private_key: str, data: str) -> str:
    key = load_private_key(private_key)

    digest = SHA256.new(
        data.encode("utf-8")
    )

    signature = pkcs1_15.new(key).sign(digest)

    return base64.b64encode(
        signature
    ).decode("utf-8")


def decrypt_rsa_oaep(
    private_key: str,
    encrypted_data: str
) -> str:
    key = load_private_key(private_key)

    from Crypto.Cipher import PKCS1_OAEP

    cipher = PKCS1_OAEP.new(key)

    result = cipher.decrypt(
        base64.b64decode(encrypted_data)
    )

    return result.decode("utf-8")