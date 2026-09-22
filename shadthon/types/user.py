class User:
    def __init__(
        self,
        guid=None,
        name=None,
        username=None,
        bio=None,
        phone=None,
        is_verified=False,
        raw=None,
        **kwargs,
    ):
        self.guid = guid
        self.name = name
        self.username = username
        self.bio = bio
        self.phone = phone
        self.is_verified = is_verified
        self.raw = raw or kwargs

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            return cls(raw=data)

        return cls(
            guid=data.get(
                "guid",
                data.get("user_guid"),
            ),
            name=data.get(
                "name",
                data.get("first_name"),
            ),
            username=data.get("username"),
            bio=data.get("bio"),
            phone=data.get("phone"),
            is_verified=data.get(
                "is_verified",
                False,
            ),
            raw=data,
        )