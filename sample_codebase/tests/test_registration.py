from users.registration import register


def test_registration():
    user = register("newuser", "password123")

    assert user["username"] == "newuser"
