from payments.payment_service import process_payment


def payment(user_id, amount):
    return process_payment(user_id, amount)
