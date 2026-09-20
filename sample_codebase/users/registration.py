from users.user_service import register_user


def validate_registration(username, password):
    if not username:
        return False

    if len(password) < 6:
        return False

    return True


def register(username, password):
    if not validate_registration(username, password):
        raise ValueError("Invalid registration data")

    return register_user(username, password)
