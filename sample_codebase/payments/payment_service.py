def process_payment(user_id, amount):
    if amount <= 0:
        raise ValueError("Invalid payment amount")

    return {
        "user_id": user_id,
        "amount": amount,
        "status": "processed"
    }
