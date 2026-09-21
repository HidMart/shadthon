from __future__ import annotations

import json
import os


class Session:
    def __init__(self, name="default"):
        self.name = name

        base = os.path.expanduser("~/.shadthon")
        os.makedirs(base, exist_ok=True)

        self.path = os.path.join(base, f"{name}.json")
        self.data = {}
        self.load()

    @property
    def authenticated(self):
        return bool(
            self.data.get("auth")
            and self.data.get("key_hex")
        )

    @property
    def auth(self):
        return self.data.get("auth", "")

    @property
    def decode_auth(self):
        return self.data.get("decode_auth", "")

    @property
    def private_key(self):
        return self.data.get("private_key", "")

    @property
    def phone(self):
        return (
            self.data.get("phone_number")
            or self.data.get("phone")
            or ""
        )

    @property
    def user_guid(self):
        return self.data.get("user_guid", "")

    @property
    def tmp_session(self):
        return self.data.get("tmp_session", "")

    @property
    def state(self):
        try:
            return int(self.data.get("state", 0))
        except (TypeError, ValueError):
            return 0

    @state.setter
    def state(self, value):
        self.data["state"] = int(value)

    @property
    def messenger_host(self):
        return self.data.get(
            "messenger_host",
            "shadmessenger60.iranlms.ir",
        )

    @messenger_host.setter
    def messenger_host(self, value):
        self.data["messenger_host"] = value

    @property
    def key_hex(self):
        return self.data.get("key_hex", "")

    @property
    def iv_hex(self):
        return self.data.get("iv_hex", "")

    def get_key(self):
        if not self.key_hex:
            raise RuntimeError("Session encryption key is not available.")
        return bytes.fromhex(self.key_hex)

    def set_key(self, key):
        self.data["key_hex"] = key.hex()

    def get_iv(self):
        if self.iv_hex:
            return bytes.fromhex(self.iv_hex)
        return b"\x00" * 16

    def set_iv(self, iv):
        self.data["iv_hex"] = iv.hex()

    def load(self):
        if not os.path.exists(self.path):
            return

        try:
            with open(self.path, "r", encoding="utf-8") as file:
                self.data = json.load(file)
        except Exception:
            self.data = {}

    def save(self):
        temporary = self.path + ".tmp"

        with open(temporary, "w", encoding="utf-8") as file:
            json.dump(
                self.data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        os.replace(temporary, self.path)

    def set_auth(
        self,
        auth,
        private_key,
        phone=None,
        user_guid=None,
        public_key=None,
    ):
        self.data["auth"] = auth
        self.data["decode_auth"] = auth

        self.data["private_key"] = private_key

        if phone:
            self.data["phone_number"] = phone

        if user_guid:
            self.data["user_guid"] = user_guid

        if public_key:
            self.data["public_key"] = public_key

        self.save()

    def clear(self):
        self.data = {}

        if os.path.exists(self.path):
            os.remove(self.path)