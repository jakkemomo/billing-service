"""Module with service API paths definition"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from src.clients import get_payment_gateway
from src.db.models import Orders
from src.db.repositories.order import OrderRepository
from src.db.repositories.payment_method import PaymentMethodRepository
from src.db.repositories.subscription import SubscriptionRepository
from src.models.common import OrderState, SubscriptionState
from src.resources.error_messages import (
    INACTIVE_PRODUCT,
    ORDER_IS_PAID,
    ORDER_NOT_FOUND,
    PAYMENT_METHOD_NOT_FOUND,
    SUBSCRIPTION_NOT_FOUND,
    USER_HAS_ROLE,
    USER_OR_ROLE_NOT_FOUND,
)
from src.services.roles import (
    RoleServiceConflictError,
    RoleServiceNotFoundError,
    RolesService,
    get_roles_service,
)
from tortoise.transactions import in_transaction

service_router = APIRouter(prefix="/service", tags=["service"])

logger = logging.getLogger(__name__)


@service_router.post("/order/{order_id}/update_info", status_code=200)
async def update_order_info(order_id: str):
    """Order information updating by service applications."""
    order = await OrderRepository.get(order_id)
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=ORDER_NOT_FOUND)

    if order.state == OrderState.PAID:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=ORDER_IS_PAID)

    payment_gateway = get_payment_gateway(order.payment_system)

    logger.info(f"Updating order {order.id} through {order.payment_system}.")

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
            logger.info(
                f"Payment method {payment_method.id} for order {order.id} / user {order.user_id} created successfully."
            )

            await SubscriptionRepository.pre_activate(order.subscription.id)

        logger.info(f"VALUES: {order}, {order_status}, {payment_method}")
        if payment_method:
            await OrderRepository.update(
                order.id,
                state=order_status,
                payment_method=payment_method,
            )
            logger.info(
                f"Order {order.id} updated successfully with state {order_status.value} "
                f"and payment method {payment_method.id}."
            )

        else:
            await OrderRepository.update(
                order.id,
                state=order_status,
            )
            logger.info(
                f"Order {order.id} updated successfully with state {order_status.value}."
            )


@service_router.post("/order/{order_id}/cancel", status_code=200)
async def cancel_order(order_id: str):
    """Order is moving to the Error state by service application."""
    order = await OrderRepository.get(order_id)
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=ORDER_NOT_FOUND)

    if order.state == OrderState.PAID:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=ORDER_IS_PAID)

    await OrderRepository.update(
        order.id,
        state=OrderState.ERROR,
    )
    logger.info(f"Order {order.id} has been marked with state Error.")


@service_router.post("/subscription/{subscription_id}/activate", status_code=200)
async def activate_subscription(
    subscription_id: str,
    roles_service: RolesService = Depends(get_roles_service),
):
    """Change subscription state to `active`."""
    subscription = await SubscriptionRepository.get(subscription_id)
    if not subscription:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=SUBSCRIPTION_NOT_FOUND)

    logger.info(f"Activating subscription {subscription.id}.")
    async with in_transaction():
        await SubscriptionRepository.activate(
            subscription.id, subscription.product.period
        )
        if subscription.state in [
            SubscriptionState.INACTIVE,
            SubscriptionState.PRE_ACTIVE,
        ]:
            logger.info(f"Granting role for user with subscription {subscription.id}.")
            try:
                await roles_service.grant_role(
                    subscription.user_id, subscription.product.role_id
                )
            except RoleServiceConflictError as e:
                logger.info(
                    f"User {subscription.user_id} already has the role {subscription.product.role_id}."
                    f"Auth service response: {e.msg}"
                )
                raise HTTPException(status.HTTP_409_CONFLICT, detail=USER_HAS_ROLE)
            except RoleServiceNotFoundError as e:
                logger.error(
                    f"User {subscription.user_id} or role {subscription.product.role_id} not found"
                    f"Auth service response: {e.msg}"
                )
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, detail=USER_OR_ROLE_NOT_FOUND
                )

        logger.info(f"Subscription {subscription_id} was activated successfully")


@service_router.post(
    "/subscription/{subscription_id}/recurring_payment", status_code=200
)
async def withdraw_subscription_price(subscription_id: str):
    """Recurring payment for subscription created by service applications"""
    subscription = await SubscriptionRepository.get(subscription_id)
    if not subscription:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=SUBSCRIPTION_NOT_FOUND)

    if not subscription.product.active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=INACTIVE_PRODUCT)

    payment_method = await PaymentMethodRepository.get_default(subscription.user_id)
    if not payment_method:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=PAYMENT_METHOD_NOT_FOUND)

    previous_order: Orders = await OrderRepository.get_subscription_order(
        subscription.user_id, subscription_id
    )
    logger.info(
        f"Making a recurring payment for subscription {subscription.id} with payment method {payment_method.id}"
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
        logger.info(
            f"Recurring payment for subscription {subscription.id} created successfully: "
            f"Payment {payment.id} / Order {order.id}"
        )


@service_router.post("/subscription/{subscription_id}/deactivate", status_code=200)
async def deactivate_subscription(
    subscription_id: str,
    roles_service: RolesService = Depends(get_roles_service),
):
    """Subscription deactivating by service applications"""
    subscription = await SubscriptionRepository.get(subscription_id)
    if not subscription:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=SUBSCRIPTION_NOT_FOUND)

    logger.info(f"Deactivating subscription {subscription.id}.")
    async with in_transaction():
        await SubscriptionRepository.deactivate(subscription_id)

        try:
            await roles_service.revoke_role(
                subscription.user_id, subscription.product.role_id
            )
        except RoleServiceNotFoundError as e:
            logger.error(
                f"User {subscription.user_id} or role {subscription.product.role_id} not found"
                f"Auth service response: {e.msg}"
            )
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail=USER_OR_ROLE_NOT_FOUND
            )

        logger.info(f"Subscription {subscription_id} was deactivated successfully")
