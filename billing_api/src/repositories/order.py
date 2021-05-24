from decimal import Decimal
from typing import Optional
from uuid import uuid4

from src.orm.models import Orders, OrderState, PaymentMethods
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
                is_refund=False,
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
        amount: Decimal,
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
    async def update(order_id: str, **kwargs):
        await Orders.filter(pk=order_id).update(
            **kwargs,
            modified=timezone.now(),
        )

    @staticmethod
    async def get_unpaid_order(user_id: str) -> Orders:
        return await Orders.get_or_none(
            user_id=user_id,
            state__in=[OrderState.DRAFT, OrderState.PROCESSING],
            is_refund=False,
            is_automatic=False,
        ).prefetch_related(
            "product",
        )

    @staticmethod
    async def create_refund_order(order: Orders, amount: Decimal) -> Orders:
        refund_order = await Orders.create(
            id=uuid4(),
            user_id=order.user_id,
            subscription=order.subscription,
            external_id=None,
            product=order.product,
            payment_system=order.payment_system,
            payment_method=order.payment_method,
            payment_amount=amount,
            payment_currency_code=order.payment_currency_code,
            user_email=order.user_email,
            state=OrderState.DRAFT,
            src_order=order,
            is_automatic=False,
            is_refund=True,
            created=timezone.now(),
            modified=timezone.now(),
        )
        return refund_order

    @staticmethod
    async def create_recurring_order(
        order: Orders, payment_method: PaymentMethods
    ) -> Orders:
        recurring_order = await Orders.create(
            id=uuid4(),
            user_id=order.user_id,
            subscription=order.subscription,
            external_id=None,
            product=order.product,
            payment_system=payment_method.payment_system,
            payment_method=payment_method,
            payment_amount=order.product.price,
            payment_currency_code=order.product.currency_code,
            user_email=order.user_email,
            state=OrderState.DRAFT,
            src_order=None,
            is_automatic=True,
            is_refund=False,
            created=timezone.now(),
            modified=timezone.now(),
        )
        return recurring_order
