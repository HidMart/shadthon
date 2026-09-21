from __future__ import annotations

import base64
import hashlib
import secrets
import string

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA1, SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Util.Padding import pad, unpad


class Crypto:
    IV = b"\x00" * 16

    @staticmethod
    def decode_auth(value: str) -> str:
        result = []

        for char in value:
            if "a" <= char <= "z":
                result.append(
                    chr(((32 - (ord(char) - 97)) % 26) + 97)
                )
            elif "A" <= char <= "Z":
                result.append(
                    chr(((29 - (ord(char) - 65)) % 26) + 65)
                )
            elif "0" <= char <= "9":
                result.append(
                    chr(((13 - (ord(char) - 48)) % 10) + 48)
                )
            else:
                result.append(char)

        return "".join(result)

    auth_set = decode_auth

    @staticmethod
    def derive_passphrase(value: str) -> str:
        if len(value) != 32:
            raise ValueError(
                "Session value must contain exactly 32 characters."
            )

        chunks = [
            value[i:i + 8]
            for i in range(0, 32, 8)
        ]

        source = (
            chunks[2]
            + chunks[0]
            + chunks[3]
            + chunks[1]
        )

        result = []

        for char in source:
            if "a" <= char <= "z":
                result.append(
                    chr(((ord(char) - 97 + 9) % 26) + 97)
                )
            else:
                result.append(char)

        return "".join(result)

    @staticmethod
    def derive_session_key(value: str) -> bytes:
        return Crypto.derive_passphrase(value).encode("utf-8")

    @staticmethod
    def make_key(auth: str) -> str:
        if len(auth) < 32:
            raise ValueError(
                "auth must contain at least 32 characters"
            )

        value = (
            auth[16:24]
            + auth[0:8]
            + auth[24:32]
            + auth[8:16]
        )

        result = []

        for char in value:
            if "0" <= char <= "9":
                result.append(
                    chr(((ord(char) - 48 + 5) % 10) + 48)
                )
            elif "a" <= char <= "z":
                result.append(
                    chr(((ord(char) - 97 + 9) % 26) + 97)
                )
            else:
                result.append(char)

        return "".join(result)

    @staticmethod
    def random_tmp_session():
        return "".join(
            secrets.choice(string.ascii_lowercase)
            for _ in range(32)
        )

    @staticmethod
    def generate_tmp_session():
        return Crypto.random_tmp_session()

    @staticmethod
    def aes_encrypt(key, plaintext, iv=None):
        iv = iv or Crypto.IV

        cipher = AES.new(
            key,
            AES.MODE_CBC,
            iv,
        )

        return cipher.encrypt(
            pad(
                plaintext,
                AES.block_size,
            )
        )

    @staticmethod
    def aes_decrypt(key, ciphertext, iv=None):
        iv = iv or Crypto.IV

        cipher = AES.new(
            key,
            AES.MODE_CBC,
            iv,
        )

        return unpad(
            cipher.decrypt(ciphertext),
            AES.block_size,
        )

    @staticmethod
    def encrypt_payload(
        key,
        plaintext,
        iv=None,
    ):
        encrypted = Crypto.aes_encrypt(
            key,
            plaintext,
            iv,
        )

        return base64.b64encode(
            encrypted
        ).decode("ascii")

    @staticmethod
    def decrypt_payload(
        key,
        data_enc,
        iv=None,
    ):
        encrypted = base64.b64decode(data_enc)

        return Crypto.aes_decrypt(
            key,
            encrypted,
            iv,
        )

    @staticmethod
    def compute_sign(key, data_enc):
        raw = (
            data_enc
            + base64.b64encode(key).decode("ascii")
        )

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def generate_rsa_keypair():
        key = RSA.generate(1024)

        private_der = key.export_key(
            format="DER",
            pkcs=8,
        )

        public_der = key.publickey().export_key(
            format="DER",
            pkcs=8,
        )

        pem = (
            b"-----BEGIN PUBLIC KEY-----\r\n"
            + base64.b64encode(public_der)
            + b"\r\n-----END PUBLIC KEY-----"
        )

        public_value = Crypto.decode_auth(
            base64.b64encode(pem).decode("ascii")
        )

        private_value = base64.b64encode(
            private_der
        ).decode("ascii")

        return public_value, private_value

    @staticmethod
    def load_private_key(private_key):
        raw = base64.b64decode(
            private_key.replace("\\n", "")
        )

        return RSA.import_key(raw)

    @staticmethod
    def encrypt_rsa(
        public_key,
        data,
    ):
        key = RSA.import_key(public_key)

        cipher = PKCS1_OAEP.new(
            key,
            hashAlgo=SHA1,
        )

        encrypted = cipher.encrypt(
            data.encode("utf-8")
            if isinstance(data, str)
            else data
        )

        return base64.b64encode(
            encrypted
        ).decode("ascii")

    @staticmethod
    def decrypt_rsa(
        private_key,
        data,
    ):
        key = Crypto.load_private_key(
            private_key
        )

        cipher = PKCS1_OAEP.new(
            key,
            hashAlgo=SHA1,
        )

        encrypted = base64.b64decode(data)

        decrypted = cipher.decrypt(
            encrypted
        )

        return decrypted.decode("utf-8")

    @staticmethod
    def sign_rsa(
        private_key,
        data,
    ):
        key = Crypto.load_private_key(
            private_key
        )

        if isinstance(data, str):
            data = data.encode("utf-8")

        digest = SHA256.new(data)

        signature = pkcs1_15.new(
            key
        ).sign(digest)

        return base64.b64encode(
            signature
        ).decode("ascii")