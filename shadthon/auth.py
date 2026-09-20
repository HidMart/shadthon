from .exceptions import AuthenticationError


class AuthManager:
    def __init__(
        self,
        methods,
        session,
    ):
        self.methods = methods
        self.session = session

    async def request_code(
        self,
        phone_number: str,
    ):
        try:
            return await self.methods.request_code(
                phone_number
            )

        except Exception as exc:
            raise AuthenticationError(
                f"Unable to request login code: {exc}"
            ) from exc

    async def login(
        self,
        phone_number: str,
        otp: str,
        phone_code_hash: str,
    ):
        try:
            return await self.methods.sign_in(
                phone_number,
                otp,
                phone_code_hash,
            )

        except Exception as exc:
            raise AuthenticationError(
                f"Unable to complete login: {exc}"
            ) from exc