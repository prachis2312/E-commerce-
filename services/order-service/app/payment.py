import random


def process_payment(amount: float, payment_method: str) -> dict:
    """
    Simulates payment processing.
    In production, this would call a real gateway (Stripe, Razorpay, etc.)
    and this function would be replaced with an actual API call,
    without changing how the rest of the checkout flow uses it.
    """
    # Simulate ~95% success rate, mimicking occasional real-world payment failures
    success = random.random() < 0.95

    if success:
        return {
            "success": True,
            "transaction_id": f"txn_{random.randint(100000, 999999)}",
            "message": "Payment processed successfully"
        }
    else:
        return {
            "success": False,
            "transaction_id": None,
            "message": "Payment failed. Please try again or use a different payment method."
        }