class ShadthonError(Exception):
    pass


class AuthenticationError(ShadthonError):
    pass


class NetworkError(ShadthonError):
    pass


class APIError(ShadthonError):
    pass


class SessionError(ShadthonError):
    pass