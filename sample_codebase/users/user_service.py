USERS = [
    {
        "id": 1,
        "username": "mayank",
        "password": "demo123"
    }
]


def find_user(username):
    for user in USERS:
        if user["username"] == username:
            return user

    return None


def register_user(username, password):
    if find_user(username):
        raise ValueError("User already exists")

    user = {
        "id": len(USERS) + 1,
        "username": username,
        "password": password
    }

    USERS.append(user)

    return user
