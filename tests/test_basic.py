from shadthon import Client, Session


def test_session():
    session = Session(
        phone_number="09123456789"
    )

    assert session.phone_number == (
        "09123456789"
    )

    assert not session.has_auth()


def test_client():
    client = Client(
        "09123456789"
    )

    assert client.phone_number == (
        "09123456789"
    )