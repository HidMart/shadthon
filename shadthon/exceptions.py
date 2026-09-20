class ShadthonError(Exception):
    pass


class AuthenticationError(ShadthonError):
    pass


class APIError(ShadthonError):
    pass


class NetworkError(ShadthonError):
    pass


class CryptoError(ShadthonError):
    pass