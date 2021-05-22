from src.adapters.abstract import AbstractAdapter
from src.adapters.stripe import get_stripe_adapter
from src.models.common import OrderState, Payment, PaymentMethod, Refund
from src.orm.models import Orders


class PaymentGatewayService:
    def __init__(self, order: Orders, client: AbstractAdapter):
        self.order = order
        self.client = client

    async def create_service_payment(self) -> Payment:
        return await self.client.create_payment(self.order)

    async def create_automatic_service_payment(self) -> Payment:
        return await self.client.create_recurring_payment(self.order)

    async def get_order_status(self) -> OrderState:
        return await self.client.get_payment_status(self.order)

    async def get_order(self) -> Payment:
        return await self.client.get_payment(self.order)

    async def get_order_payment_method(self) -> PaymentMethod:
        return await self.client.get_payment_method(self.order)

    async def create_service_refund(self) -> Refund:
        return await self.client.create_refund(self.order)

    async def get_refund_status(self) -> OrderState:
        return await self.client.get_refund_status(self.order)


def get_payment_gateway(order: Orders) -> AbstractAdapter:
    if order.payment_system == "stripe":
        return get_stripe_adapter()
    else:
        raise ValueError(f"Could not find payment service for order {order.id}")


async def get_payment_gateway_service(order: Orders) -> PaymentGatewayService:
    client = get_payment_gateway(order)
    return PaymentGatewayService(order, client)
