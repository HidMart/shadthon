from dataclasses import dataclass
from typing import Any


@dataclass
class LoginResult:
    phone: str
    phone_code_hash: str
    raw: Any = None


@dataclass
class Session:
    auth: str
    private_key: str
    phone: str