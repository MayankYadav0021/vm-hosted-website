from payments.payment_service import process_payment


def test_payment():
    result = process_payment(1, 500)

    assert result["status"] == "processed"
