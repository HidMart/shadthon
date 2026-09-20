from __future__ import annotations

import base64
from typing import Any

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class CryptoError(Exception):
    pass


class Crypto:
    def __init__(self, auth: str):
        if not isinstance(auth, str):
            raise CryptoError("auth must be a string")

        if len(auth) < 32:
            raise CryptoError(
                "Invalid auth: auth must contain at least 32 characters."
            )

        source = (
            auth[16:24]
            + auth[0:8]
            + auth[24:32]
            + auth[8:16]
        )

        if len(source) != 32:
            raise CryptoError("Unable to derive Shad v5 key.")

        try:
            key = "".join(
                chr(((ord(char) - 97 + 9) % 26) + 97)
                for char in source
            )
        except Exception as exc:
            raise CryptoError(
                "Unable to derive encryption key."
            ) from exc

        self.key = key.encode("utf-8")
        self.iv = b"\x00" * 16

        if len(self.key) != 32:
            raise CryptoError(
                "Derived AES key must be 32 bytes."
            )

    def encrypt(self, text: str | bytes) -> str:
        if isinstance(text, str):
            data = text.encode("utf-8")
        else:
            data = text

        cipher = AES.new(
            self.key,
            AES.MODE_CBC,
            self.iv,
        )

        encrypted = cipher.encrypt(
            pad(data, AES.block_size)
        )

        return base64.b64encode(
            encrypted
        ).decode("utf-8")

    def decrypt(self, text: str) -> str:
        try:
            encrypted = base64.b64decode(
                text.encode("utf-8")
            )

            cipher = AES.new(
                self.key,
                AES.MODE_CBC,
                self.iv,
            )

            decrypted = cipher.decrypt(
                encrypted
            )

            return unpad(
                decrypted,
                AES.block_size,
            ).decode("utf-8")

        except Exception as exc:
            raise CryptoError(
                "Unable to decrypt Shad response."
            ) from exc


def aes_encrypt(
    text: str | bytes,
    key: bytes,
    iv: bytes | None = None,
) -> str:
    if isinstance(text, str):
        text = text.encode("utf-8")

    if iv is None:
        iv = b"\x00" * 16

    cipher = AES.new(
        key,
        AES.MODE_CBC,
        iv,
    )

    return base64.b64encode(
        cipher.encrypt(
            pad(text, AES.block_size)
        )
    ).decode("utf-8")


def aes_decrypt(
    encoded: str,
    key: bytes,
    iv: bytes | None = None,
) -> str:
    if iv is None:
        iv = b"\x00" * 16

    cipher = AES.new(
        key,
        AES.MODE_CBC,
        iv,
    )

    decrypted = cipher.decrypt(
        base64.b64decode(
            encoded.encode("utf-8")
        )
    )

    return unpad(
        decrypted,
        AES.block_size,
    ).decode("utf-8")


def derive_key(
    auth: str,
    decoded_auth: dict[str, Any] | None = None,
) -> tuple[bytes, bytes]:
    crypto = Crypto(auth)

    return (
        crypto.key,
        crypto.iv,
    )


def decode_auth(
    auth: str,
) -> dict[str, Any]:
    return {
        "auth": auth,
        "length": len(auth),
    }