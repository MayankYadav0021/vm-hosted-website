from auth.auth_service import authenticate


def test_authentication():
    assert authenticate("mayank", "demo123") is True
    assert authenticate("unknown", "wrong") is False
