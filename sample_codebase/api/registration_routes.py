from users.registration import register


def registration(username, password):
    user = register(username, password)

    return {
        "status": 201,
        "user": user
    }
