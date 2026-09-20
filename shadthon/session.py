import json
import os


class Session:
    def __init__(self, name="default"):
        self.name = name

        base = os.path.expanduser(
            "~/.shadthon"
        )

        os.makedirs(
            base,
            exist_ok=True,
        )

        self.path = os.path.join(
            base,
            f"{name}.json",
        )

        self.data = {}

        self.load()

    @property
    def authenticated(self):
        return bool(
            self.data.get("auth")
        )

    @property
    def auth(self):
        return self.data.get("auth")

    @property
    def private_key(self):
        return self.data.get(
            "private_key"
        )

    @property
    def phone(self):
        return self.data.get(
            "phone"
        )

    def load(self):
        if not os.path.exists(self.path):
            return

        try:
            with open(
                self.path,
                "r",
                encoding="utf-8",
            ) as file:
                self.data = json.load(file)

        except Exception:
            self.data = {}

    def save(self):
        temporary = self.path + ".tmp"

        with open(
            temporary,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                self.data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        os.replace(
            temporary,
            self.path,
        )

    def set_auth(
        self,
        auth,
        private_key,
        phone=None,
    ):
        self.data["auth"] = auth
        self.data["private_key"] = private_key

        if phone:
            self.data["phone"] = phone

        self.save()

    def clear(self):
        self.data = {}

        if os.path.exists(self.path):
            os.remove(self.path)