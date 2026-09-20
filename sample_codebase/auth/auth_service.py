from users.user_service import find_user


def authenticate(username, password):
    user = find_user(username)

    if user is None:
        return False

    return user["password"] == password
