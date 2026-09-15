from .api import ShadHTTP
from .crypto import ShadCrypto
from .session import SessionStorage
from .exceptions import ShadAuthError
from .models import LoginResult


class Shad:

    def __init__(
        self,
        api_url="https://shadmessenger2.iranlms.ir/",
        session_file="shad_session.json"
    ):

        self.api = ShadHTTP(api_url)

        self.crypto = ShadCrypto()

        self.session = SessionStorage(
            session_file
        )

        self.phone = None
        self.phone_code_hash = None
        self.auth = None
        self.private_key = None

    async def login(self, phone):

        phone = phone.replace(
            " ",
            ""
        ).replace(
            "-",
            ""
        )

        if phone.startswith("0"):
            phone = "98" + phone[1:]

        if phone.startswith("+"):
            phone = phone[1:]

        if not phone.startswith("98"):
            raise ShadAuthError(
                "Phone must start with 98"
            )

        self.phone = phone

        raise ShadAuthError(
            "The exact v6 sendCode encryption envelope "
            "must be implemented before login can be sent."
        )

    async def verify(self, code):

        if not self.phone:
            raise ShadAuthError(
                "Call login(phone) first"
            )

        if not code:
            raise ShadAuthError(
                "Verification code is required"
            )

        raise ShadAuthError(
            "The exact v6 signIn envelope is not yet "
            "implemented."
        )

    async def send_message(
        self,
        chat_id,
        text
    ):

        if not self.auth:
            raise ShadAuthError(
                "You are not logged in"
            )

        raise ShadAuthError(
            "Authenticated v6 request serializer "
            "is not configured."
        )

    def save_session(self):

        if not self.auth:
            raise ShadAuthError(
                "No authenticated session"
            )

        self.session.save({
            "phone": self.phone,
            "auth": self.auth,
            "private_key": self.private_key
        })

    def load_session(self):

        data = self.session.load()

        if not data:
            return False

        self.phone = data.get("phone")
        self.auth = data.get("auth")
        self.private_key = data.get(
            "private_key"
        )

        self.crypto.set_auth(
            self.auth
        )

        self.crypto.set_private_key(
            self.private_key
        )

        return True