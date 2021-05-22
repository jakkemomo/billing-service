from fastapi import APIRouter, Depends, HTTPException
from src.models.common import OrderState, SubscriptionState
from src.orm.models import Orders
from src.repositories.order import OrderRepository
from src.repositories.payment_method import PaymentMethodRepository
from src.repositories.subscription import SubscriptionRepository
from src.services.payment_gateway import (
    PaymentGatewayService,
    get_payment_gateway_service,
)
from src.services.roles import RolesService, get_roles_service

service_router = APIRouter()


@service_router.put("/service/order/{order_id}/status")
async def update_order_status(
    order_id: str,
    roles_service: RolesService = Depends(get_roles_service),
):
    """ Payment status updating by service applications """
    order = await OrderRepository.get(order_id)

    payment_service: PaymentGatewayService = await get_payment_gateway_service(order)
    order_status = await payment_service.get_order_status()

    if order_status == OrderState.PAID:
        if not order.is_automatic:
            user_payment_method = await payment_service.get_order_payment_method()

            payment_method = await PaymentMethodRepository.create(
                user_id=order.user_id,
                external_id=user_payment_method.id,
                payment_type=user_payment_method.type,
                payment_system=order.payment_system,
                data=user_payment_method.data,
            )

            await OrderRepository.update_payment_method(order.id, payment_method.id)

        await SubscriptionRepository.activate(
            order.subscription.id, order.product.period
        )
        await roles_service.grant_role(order.user_id, order.product.role_id)

    await OrderRepository.update_state(order.id, order_status)


@service_router.put("/service/subscription/{subscription_id}")
async def update_subscription(subscription_id: str):
    """ Update subscription with recurring payment created by service applications """

    subscription = await SubscriptionRepository.get(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=404,
            detail="Subscription not found",
        )

    if not subscription.product.active:
        raise HTTPException(
            status_code=402,
            detail="Product is not active",
        )

    payment_method = await PaymentMethodRepository.get_default(subscription.user_id)
    if not payment_method:
        raise HTTPException(
            status_code=404,
            detail="Default payment method not found",
        )

    previous_order: Orders = await OrderRepository.get_subscription_order(
        subscription.user_id, subscription_id
    )
    order = await OrderRepository.create(
        user_id=subscription.user_id,
        product_id=subscription.product.id,
        subscription_id=subscription_id,
        payment_system=payment_method.payment_system,
        amount=subscription.product.price,
        payment_currency_code=subscription.product.currency_code,
        payment_method_id=payment_method.id,
        is_automatic=True,
        user_email=previous_order.user_email,
    )

    payment_service: PaymentGatewayService = await get_payment_gateway_service(order)
    payment = await payment_service.create_automatic_service_payment()

    if payment.state == OrderState.PAID:
        await SubscriptionRepository.activate(
            subscription_id, subscription.product.period
        )

    await OrderRepository.update_state(order.id, payment.state)


@service_router.put("/service/order/{order_id}/status")
async def update_order_status(order_id: str):
    """ Payment status updating by service applications """
    db_order = await OrderRepository.get(order_id)
    payment_service: PaymentGatewayService = await get_payment_gateway_service(db_order)

    if db_order.is_refund:
        status = await payment_service.get_refund_status()
    else:
        status = await payment_service.get_order_status()

    await OrderRepository.update_state(db_order.id, status)


@service_router.delete("/service/subscription/{subscription_id}")
async def cancel_subscription(
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

    await SubscriptionRepository.deactivate(
        subscription_id,
        SubscriptionState.INACTIVE,
    )

    await roles_service.revoke_role(subscription.user_id, subscription.product.role_id)
