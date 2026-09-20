import base64
import hashlib

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


BLOCK_SIZE = 16


def encode_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def decode_base64(data: str) -> bytes:
    return base64.b64decode(data)


def derive_passphrase(value: str) -> str:
    if len(value) != 32:
        raise ValueError(
            "Session value must contain exactly 32 characters."
        )

    chunks = [
        value[0:8],
        value[8:16],
        value[16:24],
        value[24:32],
    ]

    reordered = (
        chunks[2]
        + chunks[0]
        + chunks[3]
        + chunks[1]
    )

    output = []

    for char in reordered:
        if "a" <= char <= "z":
            output.append(
                chr(
                    ((ord(char) - ord("a") + 9) % 26)
                    + ord("a")
                )
            )
        else:
            output.append(char)

    return "".join(output)


def decode_auth(value: str) -> str:
    lower_source = "abcdefghijklmnopqrstuvwxyz"
    lower_target = "zyxwvutsrqponmlkjihgfedcba"

    upper_source = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    upper_target = "ZYXWVUTSRQPONMLKJIHGFEDCBA"

    result = []

    for char in value:
        if char in lower_source:
            index = lower_source.index(char)
            result.append(lower_target[index])

        elif char in upper_source:
            index = upper_source.index(char)
            result.append(upper_target[index])

        elif char.isdigit():
            result.append(
                str((int(char) + 13) % 10)
            )

        else:
            result.append(char)

    return "".join(result)


def derive_key(value: str) -> bytes:
    return derive_passphrase(value).encode("utf-8")


def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=1024,
    )

    public_key = private_key.public_key()

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_value = decode_auth(
        encode_base64(public_pem)
    )

    return (
        public_value,
        private_pem.decode("utf-8"),
    )


def rsa_decrypt(
    private_key_pem: str,
    encrypted_value: str,
) -> str:
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"),
        password=None,
    )

    encrypted = base64.b64decode(encrypted_value)

    decrypted = private_key.decrypt(
        encrypted,
        padding.OAEP(
            mgf=padding.MGF1(
                algorithm=hashes.SHA1()
            ),
            algorithm=hashes.SHA1(),
            label=None,
        ),
    )

    return decrypted.decode("utf-8")


def rsa_sign(
    private_key_pem: str,
    data: str,
) -> str:
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"),
        password=None,
    )

    signature = private_key.sign(
        data.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    return encode_base64(signature)


def _pad(data: bytes) -> bytes:
    amount = BLOCK_SIZE - (len(data) % BLOCK_SIZE)

    return data + bytes([amount]) * amount


def _unpad(data: bytes) -> bytes:
    if not data:
        raise ValueError("Empty decrypted payload.")

    amount = data[-1]

    if amount < 1 or amount > BLOCK_SIZE:
        raise ValueError("Invalid padding.")

    if data[-amount:] != bytes([amount]) * amount:
        raise ValueError("Invalid padding.")

    return data[:-amount]


def aes_encrypt(
    data: str,
    key: bytes,
    iv: bytes = None,
) -> str:
    if iv is None:
        iv = b"\x00" * 16

    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
    )

    encryptor = cipher.encryptor()

    encrypted = encryptor.update(
        _pad(data.encode("utf-8"))
    )

    encrypted += encryptor.finalize()

    return encode_base64(encrypted)


def aes_decrypt(
    data: str,
    key: bytes,
    iv: bytes = None,
) -> str:
    if iv is None:
        iv = b"\x00" * 16

    encrypted = decode_base64(data)

    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
    )

    decryptor = cipher.decryptor()

    decrypted = decryptor.update(
        encrypted
    )

    decrypted += decryptor.finalize()

    return _unpad(decrypted).decode("utf-8")


def calculate_signature(
    key: bytes,
    data: str,
) -> str:
    raw = (
        data.encode("utf-8")
        + encode_base64(key).encode("utf-8")
    )

    return hashlib.sha256(raw).hexdigest()


def probe_decrypt(
    data: str,
    temporary_session: str,
):
    candidates = []

    try:
        candidates.append(
            (
                derive_key(temporary_session),
                b"\x00" * 16,
            )
        )
    except Exception:
        pass

    candidates.append(
        (
            temporary_session.encode("utf-8"),
            b"\x00" * 16,
        )
    )

    candidates.append(
        (
            hashlib.sha256(
                temporary_session.encode("utf-8")
            ).digest(),
            b"\x00" * 16,
        )
    )

    for key, iv in candidates:
        try:
            return aes_decrypt(
                data,
                key,
                iv,
            ), key, iv

        except Exception:
            continue

    raise ValueError(
        "Unable to decrypt server response."
    )