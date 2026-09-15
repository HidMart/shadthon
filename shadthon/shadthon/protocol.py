import json


API_VERSION = "6"


class ShadProtocol:

    @staticmethod
    def make_client(
        app_version="4.4.26",
        language="fa"
    ):
        return {
            "app_name": "Main",
            "app_version": app_version,
            "platform": "Web",
            "package": "web.shad.ir",
            "lang_code": language
        }

    @staticmethod
    def build_request(
        data_enc,
        tmp_session=None,
        auth=None
    ):
        result = {
            "api_version": API_VERSION,
            "data_enc": data_enc
        }

        if tmp_session is not None:
            result["tmp_session"] = tmp_session

        if auth is not None:
            result["auth"] = auth

        return result

    @staticmethod
    def dumps(data):
        return json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":")
        )

    @staticmethod
    def loads(data):
        if isinstance(data, bytes):
            data = data.decode("utf-8")

        return json.loads(data)