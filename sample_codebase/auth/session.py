def create_session(user_id):
    return {
        "user_id": user_id,
        "authenticated": True
    }


def destroy_session(session):
    session["authenticated"] = False
