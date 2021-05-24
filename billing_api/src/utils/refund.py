from datetime import date
from typing import Optional
from decimal import Decimal


def calculate_refund_amount(end_date: date, amount: Decimal, period: int) -> Optional[Decimal]:
    today = date.today()
    if end_date < today:
        return None

    days_rest = end_date - today
    return amount * days_rest.days / period
