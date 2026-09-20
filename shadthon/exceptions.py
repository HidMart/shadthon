class ShadthonError(Exception):
    pass


class AuthenticationError(ShadthonError):
    pass


class InvalidAuthError(AuthenticationError):
    pass


class NetworkError(ShadthonError):
    pass


class ProtocolError(ShadthonError):
    pass


class CryptoError(ShadthonError):
    pass


class SessionError(ShadthonError):
    pass