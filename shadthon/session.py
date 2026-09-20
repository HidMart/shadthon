import json
from pathlib import Path


class Session:
    def __init__(
        self,
        name: str = "shadthon"
    ):
        self.name = name

        self.path = (
            Path.home()
            / ".shadthon"
            / f"{name}.json"
        )

        self.tmp_session = None
        self.auth = None
        self.public_key = None
        self.private_key = None
        self.phone_number = None
        self.phone_code_hash = None
        self.user_guid = None

    @property
    def authenticated(self):
        return bool(self.auth)

    def save(self):
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        data = {
            "tmp_session": self.tmp_session,
            "auth": self.auth,
            "public_key": self.public_key,
            "private_key": self.private_key,
            "phone_number": self.phone_number,
            "phone_code_hash": self.phone_code_hash,
            "user_guid": self.user_guid,
        }

        self.path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

    def load(self):
        if not self.path.exists():
            return False

        data = json.loads(
            self.path.read_text(
                encoding="utf-8"
            )
        )

        self.tmp_session = data.get(
            "tmp_session"
        )

        self.auth = data.get(
            "auth"
        )

        self.public_key = data.get(
            "public_key"
        )

        self.private_key = data.get(
            "private_key"
        )

        self.phone_number = data.get(
            "phone_number"
        )

        self.phone_code_hash = data.get(
            "phone_code_hash"
        )

        self.user_guid = data.get(
            "user_guid"
        )

        return True

    def clear(self):
        if self.path.exists():
            self.path.unlink()

        self.tmp_session = None
        self.auth = None
        self.public_key = None
        self.private_key = None
        self.phone_number = None
        self.phone_code_hash = None
        self.user_guid = None