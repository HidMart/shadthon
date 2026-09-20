class ShadthonError(Exception):
    pass


class AuthenticationError(
    ShadthonError
):
    pass


class NetworkError(
    ShadthonError
):
    pass


class ProtocolError(
    ShadthonError
):
    pass


class InvalidAuthError(
    AuthenticationError
):
    pass


class RateLimitError(
    ShadthonError
):
    pass