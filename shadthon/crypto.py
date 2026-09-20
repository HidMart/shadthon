from __future__ import annotations

import base64
import hashlib
import json
import secrets
from typing import Any

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA1, SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15


BLOCK_SIZE = 16


def _pad(data: bytes) -> bytes:
    amount = BLOCK_SIZE - (
        len(data) % BLOCK_SIZE
    )

    return data + bytes([amount]) * amount


def _unpad(data: bytes) -> bytes:
    if not data:
        raise ValueError(
            "Empty decrypted data"
        )

    amount = data[-1]

    if amount < 1 or amount > BLOCK_SIZE:
        raise ValueError(
            "Invalid PKCS7 padding"
        )

    if data[-amount:] != bytes([amount]) * amount:
        raise ValueError(
            "Invalid PKCS7 padding"
        )

    return data[:-amount]


def aes_encrypt(
    text: str | bytes,
    key: bytes,
    iv: bytes | None = None,
) -> str:
    if isinstance(text, str):
        data = text.encode("utf-8")
    else:
        data = text

    if len(key) not in (16, 24, 32):
        raise ValueError(
            "AES key must be 16, 24 or 32 bytes"
        )

    if iv is None:
        iv = b"\x00" * 16

    if len(iv) != 16:
        raise ValueError(
            "AES IV must be 16 bytes"
        )

    cipher = AES.new(
        key,
        AES.MODE_CBC,
        iv,
    )

    encrypted = cipher.encrypt(
        _pad(data)
    )

    return base64.b64encode(
        encrypted
    ).decode("ascii")


def aes_decrypt(
    encoded: str,
    key: bytes,
    iv: bytes | None = None,
) -> str:
    if len(key) not in (16, 24, 32):
        raise ValueError(
            "AES key must be 16, 24 or 32 bytes"
        )

    if iv is None:
        iv = b"\x00" * 16

    if len(iv) != 16:
        raise ValueError(
            "AES IV must be 16 bytes"
        )

    encrypted = base64.b64decode(
        encoded
    )

    cipher = AES.new(
        key,
        AES.MODE_CBC,
        iv,
    )

    decrypted = cipher.decrypt(
        encrypted
    )

    return _unpad(
        decrypted
    ).decode("utf-8")


def generate_rsa_keypair(
    bits: int = 1024,
) -> tuple[str, str]:
    private_key = RSA.generate(bits)

    public_key = private_key.publickey()

    private_pem = private_key.export_key(
        format="PEM"
    ).decode("utf-8")

    public_pem = public_key.export_key(
        format="PEM"
    ).decode("utf-8")

    return (
        private_pem,
        public_pem,
    )


def generate_rsa_keys(
    bits: int = 1024,
) -> tuple[str, str]:
    return generate_rsa_keypair(bits)


def rsa_oaep_decrypt(
    encrypted_base64: str,
    private_key_pem: str,
) -> bytes:
    private_key = RSA.import_key(
        private_key_pem
    )

    encrypted = base64.b64decode(
        encrypted_base64
    )

    cipher = PKCS1_OAEP.new(
        private_key,
        hashAlgo=SHA1,
    )

    return cipher.decrypt(
        encrypted
    )


def rsa_decrypt(
    private_key_pem: str,
    encrypted_base64: str,
) -> bytes:
    return rsa_oaep_decrypt(
        encrypted_base64,
        private_key_pem,
    )


def rsa_sign(
    text: str | bytes,
    private_key_pem: str,
) -> str:
    private_key = RSA.import_key(
        private_key_pem
    )

    if isinstance(text, str):
        data = text.encode("utf-8")
    else:
        data = text

    digest = SHA256.new(data)

    signature = pkcs1_15.new(
        private_key
    ).sign(digest)

    return base64.b64encode(
        signature
    ).decode("ascii")


def decode_auth(
    auth: str,
) -> dict[str, Any]:
    raw = base64.b64decode(auth)

    try:
        text = raw.decode("utf-8")

        value = json.loads(text)

        if isinstance(value, dict):
            return value

    except Exception:
        pass

    parts = raw.split(b"|")

    result: dict[str, Any] = {
        "raw": raw.hex()
    }

    for index, part in enumerate(
        parts[:10]
    ):
        result[
            f"part_{index}"
        ] = part.decode(
            "utf-8",
            errors="ignore",
        )

    return result


def derive_key(
    auth: str,
    decoded_auth: dict[str, Any] | None = None,
) -> tuple[bytes, bytes]:
    if decoded_auth is None:
        decoded_auth = {}

    candidates = []

    for name in (
        "key",
        "auth_key",
        "session_key",
        "key_hex",
    ):
        value = decoded_auth.get(name)

        if isinstance(value, str) and value:
            candidates.append(value)

    if candidates:
        value = candidates[0]

        try:
            key = bytes.fromhex(value)

            if len(key) in (
                16,
                24,
                32,
            ):
                return (
                    key,
                    b"\x00" * 16,
                )
        except ValueError:
            pass

        digest = hashlib.sha256(
            value.encode("utf-8")
        ).digest()

        return (
            digest[:32],
            b"\x00" * 16,
        )

    raw = base64.b64decode(auth)

    digest = hashlib.sha256(
        raw
    ).digest()

    return (
        digest[:32],
        b"\x00" * 16,
    )


def derive_temporary_key(
    temporary_session: str,
) -> bytes:
    return hashlib.sha256(
        temporary_session.encode(
            "utf-8"
        )
    ).digest()


def random_token(
    length: int = 32,
) -> str:
    return secrets.token_hex(
        length
    )