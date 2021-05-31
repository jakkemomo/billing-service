"""Module with abstract client adapter definition"""

import abc

from src.db.models import Orders
from src.models.common import OrderState, Payment, PaymentMethod, Refund


class AbstractClientAdapter:
    @abc.abstractmethod
    async def get_payment_status(self, order: Orders, **kwargs) -> OrderState:
        pass

    @abc.abstractmethod
    async def create_payment(self, order: Orders, **kwargs) -> Payment:
        pass

    @abc.abstractmethod
    async def create_recurring_payment(self, order: Orders, **kwargs) -> Payment:
        pass

    @abc.abstractmethod
    async def get_refund_status(self, order: Orders, **kwargs) -> OrderState:
        pass

    @abc.abstractmethod
    async def create_refund(self, order: Orders, **kwargs) -> Refund:
        pass

    @abc.abstractmethod
    async def get_payment_method(self, order: Orders, **kwargs) -> PaymentMethod:
        pass

    @abc.abstractmethod
    async def get_payment(self, order: Orders, **kwargs) -> Payment:
        pass
