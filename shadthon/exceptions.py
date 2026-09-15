class ShadthonError(Exception):
    pass


class ShadAPIError(ShadthonError):
    pass


class ShadAuthError(ShadthonError):
    pass


class ShadProtocolError(ShadthonError):
    pass


class ShadSessionError(ShadthonError):
    pass