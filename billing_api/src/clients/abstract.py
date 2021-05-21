import abc

from models.common import OrderState
from orm.models import Orders

from .models import Payment, PaymentMethod, Refund


class AbstractClient:
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
