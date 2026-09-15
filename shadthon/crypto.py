from .exceptions import ShadProtocolError


class ShadCrypto:

    def __init__(self):
        self.auth = None
        self.private_key = None

    def set_auth(self, auth):
        self.auth = auth

    def set_private_key(self, private_key):
        self.private_key = private_key

    def encrypt(self, data, auth=None):
        raise ShadProtocolError(
            "Shad v6 encryption implementation requires "
            "the exact current Shad serializer specification."
        )

    def decrypt(self, data, auth=None):
        raise ShadProtocolError(
            "Shad v6 decryption implementation requires "
            "the exact current Shad serializer specification."
        )