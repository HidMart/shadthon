from shadthon import (
    Client,
    Message,
    Poll,
    User,
)


def test_import():
    client = Client(
        "09123456789"
    )

    assert client.phone_number == (
        "989123456789"
    )


def test_models():
    user = User.from_dict(
        {
            "user_guid": "u0-test",
            "first_name": "Test",
        }
    )

    assert user.guid == "u0-test"

    message = Message.from_dict(
        {
            "message_id": "123",
            "text": "Hello",
        }
    )

    assert message.text == "Hello"

    poll = Poll.from_dict(
        {
            "poll_id": "p1",
            "question": "Test?",
            "options": [],
        }
    )

    assert poll.poll_id == "p1"