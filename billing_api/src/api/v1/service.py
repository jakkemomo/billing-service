from fastapi import APIRouter, Depends, HTTPException
from src.clients import get_payment_gateway
from src.db.models import Orders
from src.db.repositories.order import OrderRepository
from src.db.repositories.payment_method import PaymentMethodRepository
from src.db.repositories.subscription import SubscriptionRepository
from src.models.common import OrderState, SubscriptionState
from src.services.roles import RolesService, get_roles_service
from tortoise.transactions import in_transaction

service_router = APIRouter(prefix="/service")


@service_router.post("/order/{order_id}/update_info")
async def update_order_info(order_id: str):
    """
    Order information updating by service applications.

    Order information includes:
        - order status
        - payment method if order status is PAID and order is paid by user
    """
    order = await OrderRepository.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.state == OrderState.PAID:
        raise HTTPException(status_code=409, detail="Order is paid")

    payment_gateway = get_payment_gateway(order.payment_system)

    if order.is_refund:
        order_status = await payment_gateway.get_refund_status(order)
    else:
        order_status = await payment_gateway.get_payment_status(order)

    async with in_transaction():
        payment_method = order.payment_method
        if (
            order_status == OrderState.PAID
            and not order.is_automatic
            and not order.is_refund
        ):
            user_payment_method = await payment_gateway.get_payment_method(order)

            payment_method = await PaymentMethodRepository.create(
                user_id=order.user_id,
                external_id=user_payment_method.id,
                payment_type=user_payment_method.type,
                payment_system=order.payment_system,
                data=user_payment_method.data,
            )

            await SubscriptionRepository.pre_activate(order.subscription.id)

        await OrderRepository.update(
            order.id,
            state=order_status,
            payment_method=payment_method,
        )


@service_router.post("/order/{order_id}/cancel")
async def cancel_order(order_id: str):
    """
    Order is moving to the Error state by service application.
    """
    order = await OrderRepository.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.state == OrderState.PAID:
        raise HTTPException(status_code=409, detail="Order is paid")

    await OrderRepository.update(
        order.id,
        state=OrderState.ERROR,
    )


@service_router.post("/subscription/{subscription_id}/activate")
async def activate_subscription(
    subscription_id: str,
    roles_service: RolesService = Depends(get_roles_service),
):
    subscription = await SubscriptionRepository.get(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    async with in_transaction():
        await SubscriptionRepository.activate(
            subscription.id, subscription.product.period
        )
        if subscription.state == SubscriptionState.INACTIVE:
            await roles_service.grant_role(
                subscription.user_id, subscription.product.role_id
            )


@service_router.post("/subscription/{subscription_id}/recurring_payment")
async def withdraw_subscription_price(subscription_id: str):
    """Recurring payment for subscription created by service applications"""

    subscription = await SubscriptionRepository.get(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if not subscription.product.active:
        raise HTTPException(status_code=402, detail="Product is not active")

    payment_method = await PaymentMethodRepository.get_default(subscription.user_id)
    if not payment_method:
        raise HTTPException(status_code=404, detail="Default payment method not found")

    previous_order: Orders = await OrderRepository.get_subscription_order(
        subscription.user_id, subscription_id
    )

    async with in_transaction():
        order = await OrderRepository.create_recurring_order(
            previous_order, payment_method
        )

        payment_gateway = get_payment_gateway(order.payment_system)
        payment = await payment_gateway.create_recurring_payment(order)

        await OrderRepository.update(
            order.id, external_id=payment.id, state=payment.state
        )


@service_router.post("/subscription/{subscription_id}/deactivate")
async def deactivate_subscription(
    subscription_id: str,
    roles_service: RolesService = Depends(get_roles_service),
):
    """ Subscription deactivating by service applications """
    subscription = await SubscriptionRepository.get(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=404,
            detail=f"Subscription {subscription_id} not found",
        )

    async with in_transaction():
        await SubscriptionRepository.deactivate(subscription_id)
        await roles_service.revoke_role(
            subscription.user_id, subscription.product.role_id
        )
