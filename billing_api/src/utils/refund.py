from datetime import date
from typing import Optional


def calculate_refund_amount(end_date: date, amount: float, period: int) -> Optional[float]:
    today = date.today()
    if end_date < today:
        return None

    days_rest = end_date - today
    return round(amount * days_rest.days / period, 2)
