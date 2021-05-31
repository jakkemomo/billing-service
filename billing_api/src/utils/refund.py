"""Module with refund definition way"""

from datetime import date
from decimal import Decimal
from typing import Optional


def calculate_refund_amount(end_date: date, amount: Decimal, period: int) -> Optional[Decimal]:
    """
    Refund amount calculating

    @param end_date: subscription end date
    @param amount: product full amount
    @param period: subscription period
    @return: refund amount or None if subscription has ended
    """
    today = date.today()
    if end_date < today:
        return None

    days_rest = end_date - today
    return amount * days_rest.days / period
