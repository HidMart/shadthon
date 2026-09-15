import json
from pathlib import Path

from .exceptions import ShadSessionError


class SessionStorage:

    def __init__(self, path="shad_session.json"):
        self.path = Path(path)

    def save(self, data):
        try:
            self.path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            raise ShadSessionError(str(e))

    def load(self):
        if not self.path.exists():
            return None

        try:
            return json.loads(
                self.path.read_text(encoding="utf-8")
            )
        except Exception as e:
            raise ShadSessionError(str(e))

    def exists(self):
        return self.path.exists()

    def delete(self):
        if self.path.exists():
            self.path.unlink()