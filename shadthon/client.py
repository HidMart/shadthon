from .auth import AuthManager
from .methods import Methods
from .session import Session, SessionStore
from .transport import Transport


class Client:
    def __init__(
        self,
        phone_number: str,
        session_dir: str = "sessions",
    ):
        self.phone_number = phone_number

        self.store = SessionStore(
            session_dir
        )

        self.session = (
            self.store.load(phone_number)
            or Session(
                phone_number=phone_number
            )
        )

        self.transport = Transport(
            self.session
        )

        self.methods = Methods(
            self.transport,
            self.session,
            self.store,
        )

        self.auth = AuthManager(
            self.methods,
            self.session,
        )

        self.connected = False

    async def send_code(self):
        return await self.auth.request_code(
            self.phone_number
        )

    async def login(
        self,
        otp: str,
        phone_code_hash: str,
    ):
        result = await self.auth.login(
            self.phone_number,
            otp,
            phone_code_hash,
        )

        self.connected = True

        return result

    async def start(
        self,
        otp=None,
        phone_code_hash=None,
    ):
        if self.session.has_auth():
            self.connected = True

            try:
                await self.methods.register_device()
            except Exception:
                self.session.clear_auth()
                self.store.save(
                    self.session
                )
                self.connected = False

        if not self.connected:
            result = await self.send_code()

            if otp is None:
                otp = input(
                    "Shad verification code: "
                ).strip()

            if phone_code_hash is None:
                phone_code_hash = result[
                    "phone_code_hash"
                ]

            await self.login(
                otp,
                phone_code_hash,
            )

        return self

    def is_authenticated(self):
        return self.session.has_auth()

    def logout(self):
        self.session.clear_auth()
        self.store.save(self.session)
        self.connected = False