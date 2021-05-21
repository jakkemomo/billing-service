from typing import Optional
from uuid import uuid4

from orm.models import Orders, OrderState
from tortoise import timezone


class OrderRepository:
    @staticmethod
    async def get(order_id: str) -> Optional[Orders]:
        return await Orders.get_or_none(pk=order_id).prefetch_related(
            "product",
            "subscription",
            "payment_method",
        )

    @staticmethod
    async def get_subscription_order(user_id: str, subscription_id: str) -> Orders:
        return (
            await Orders.filter(
                subscription_id=subscription_id,
                user_id=user_id,
                state=OrderState.PAID,
            )
            .order_by(
                "-created",
            )
            .prefetch_related(
                "product",
                "subscription",
                "payment_method",
            )
            .first()
        )

    @staticmethod
    async def create(
        user_id: str,
        product_id: str,
        subscription_id: str,
        payment_system: str,
        amount: float,
        payment_currency_code: str,
        state: OrderState = OrderState.DRAFT,
        external_id: Optional[str] = None,
        user_email: Optional[str] = None,
        payment_method_id: str = None,
        src_order: Orders = None,
        is_automatic: bool = False,
        is_refund: bool = False,
    ) -> Orders:
        order = await Orders.create(
            id=uuid4(),
            user_id=user_id,
            subscription_id=subscription_id,
            external_id=external_id,
            product_id=product_id,
            payment_system=payment_system,
            payment_method_id=payment_method_id,
            payment_amount=amount,
            payment_currency_code=payment_currency_code,
            user_email=user_email,
            state=state,
            src_order=src_order,
            is_automatic=is_automatic,
            is_refund=is_refund,
            created=timezone.now(),
            modified=timezone.now(),
        )
        await order.fetch_related("product", "subscription", "payment_method")
        return order

    @staticmethod
    async def update_state(order_id: str, state: OrderState):
        await Orders.filter(pk=order_id).update(
            state=state,
            modified=timezone.now(),
        )

    @staticmethod
    async def update(order_id: str, **kwargs):
        await Orders.filter(pk=order_id).update(
            **kwargs,
            modified=timezone.now(),
        )

    @staticmethod
    async def update_payment_method(order_id: str, payment_method_id: str):
        await Orders.filter(pk=order_id).update(
            payment_method_id=payment_method_id,
            modified=timezone.now(),
        )

    @staticmethod
    async def get_unpaid_order(user_id: str) -> Orders:
        return await Orders.get_or_none(
            user_id=user_id, state__in=[OrderState.DRAFT, OrderState.PROCESSING]
        )
