ROLE_PERMISSIONS = {
    "admin": {"read", "write", "delete"},
    "doctor": {"read", "write"},
    "billing": {"read", "billing"},
    "receptionist": {"read", "write"},
}


def authenticate(token):
    valid_tokens = {
        "admin-token": "admin",
        "doctor-token": "doctor",
        "billing-token": "billing",
        "reception-token": "receptionist",
    }

    return valid_tokens.get(token)


def authorize(role, permission):
    permissions = ROLE_PERMISSIONS.get(role, set())
    return permission in permissions
