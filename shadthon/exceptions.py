class ShadthonError(Exception):
    pass


class APIError(ShadthonError):
    pass


class NetworkError(ShadthonError):
    pass


class AuthenticationError(ShadthonError):
    pass