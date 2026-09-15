import base64
import json

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from .exceptions import ShadProtocolError


class ShadCrypto:

    def __init__(self):
        self.auth = None
        self.private_key = None
        self.tmp_session = None

    def set_auth(self, auth):
        self.auth = auth

    def set_private_key(self, private_key):
        self.private_key = private_key

    def set_tmp_session(self, tmp_session):
        self.tmp_session = tmp_session

    def get_tmp_session(self):
        return self.tmp_session

    def create_secret_passphrase(self, value):
        if not value:
            return value

        a = value[0:8]
        b = value[8:16]

        result = (
            value[16:24]
            + a
            + value[24:32]
            + b
        )

        output = []

        for char in result:

            if "0" <= char <= "9":
                char = chr(
                    (
                        ord(char)
                        - ord("0")
                        + 5
                    ) % 10
                    + ord("0")
                )

            elif "a" <= char <= "z":
                char = chr(
                    (
                        ord(char)
                        - ord("a")
                        + 9
                    ) % 26
                    + ord("a")
                )

            output.append(char)

        return "".join(output)

    def encrypt(self, data, not_authorized=False):

        secret = (
            self.tmp_session
            if not_authorized
            else self.auth
        )

        if not secret:
            return data

        return self.enc_by_auth(
            data,
            secret
        )

    def decrypt(self, data, not_authorized=False):

        secret = (
            self.tmp_session
            if not_authorized
            else self.auth
        )

        if not secret:
            return data

        return self.dec(
            data,
            secret
        )

    def enc_by_auth(self, data, secret):

        if not secret:
            return data

        key_string = self.create_secret_passphrase(
            secret
        )

        key = key_string.encode("utf-8")

        plaintext = json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":")
        ).encode("utf-8")

        iv = bytes(16)

        cipher = AES.new(
            key,
            AES.MODE_CBC,
            iv
        )

        encrypted = cipher.encrypt(
            pad(
                plaintext,
                AES.block_size
            )
        )

        return base64.b64encode(
            encrypted
        ).decode("ascii")

    def enc(self, text, secret):

        if not secret:
            return text

        key = secret.encode("utf-8")
        iv = bytes(16)

        cipher = AES.new(
            key,
            AES.MODE_CBC,
            iv
        )

        encrypted = cipher.encrypt(
            pad(
                text.encode("utf-8"),
                AES.block_size
            )
        )

        return base64.b64encode(
            encrypted
        ).decode("ascii")

    def dec(self, data, secret):

        if not secret:
            return data

        try:
            key_string = self.create_secret_passphrase(
                secret
            )

            key = key_string.encode("utf-8")

            try:
                ciphertext = base64.b64decode(
                    data
                )
            except Exception:
                ciphertext = data

            iv = bytes(16)

            cipher = AES.new(
                key,
                AES.MODE_CBC,
                iv
            )

            plaintext = unpad(
                cipher.decrypt(ciphertext),
                AES.block_size
            )

            return plaintext.decode("utf-8")

        except Exception as e:
            raise ShadProtocolError(
                f"Shad v6 decrypt failed: {e}"
            )