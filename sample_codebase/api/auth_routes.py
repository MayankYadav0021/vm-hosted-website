from auth.auth_service import authenticate
from auth.session import create_session


def login(username, password):
    if not authenticate(username, password):
        return {
            "status": 401,
            "message": "Invalid credentials"
        }

    return {
        "status": 200,
        "session": create_session(username)
    }
