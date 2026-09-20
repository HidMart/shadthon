from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    user_guid: str = ""
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    phone_number: str = ""

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls()

        return cls(
            user_guid=data.get(
                "user_guid",
                "",
            ),
            first_name=data.get(
                "first_name",
                "",
            ),
            last_name=data.get(
                "last_name",
                "",
            ),
            username=data.get(
                "username",
                "",
            ),
            phone_number=data.get(
                "phone_number",
                "",
            ),
        )


@dataclass
class LoginResult:
    success: bool
    user: Optional[User] = None
    raw: Optional[dict] = None