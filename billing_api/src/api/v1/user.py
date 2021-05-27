from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import parse_obj_as
from src.clients import get_payment_gateway
from src.core.settings import logger
from src.db.models import PaymentMethods, Products
from src.db.repositories.order import OrderRepository
from src.db.repositories.payment_method import PaymentMethodRepository
from src.db.repositories.product import ProductRepository
from src.db.repositories.subscription import SubscriptionRepository
from src.models.api import (
    PaymentInfoIn,
    PaymentInfoOut,
    PaymentMethodOut,
    ProductOut,
    SubscriptionOut,
)
from src.models.common import OrderState
from src.services.auth import AuthorizedUser, get_user
from src.utils.refund import calculate_refund_amount
from tortoise.transactions import in_transaction

user_router = APIRouter(prefix="/user")


@user_router.post("/payment", response_model=PaymentInfoOut)
async def create_payment(
    payment_info_in: PaymentInfoIn,
    user: AuthorizedUser = Depends(get_user),
):
    """ Payment creating by user """
    if not user:
        logger.debug(f"Error while making a payment. User with email {payment_info_in.email} is not authorized.")
        raise HTTPException(status_code=403, detail="Unauthorized user")

    subscription = await SubscriptionRepository.get_user_subscription(user.id)
    if subscription:
        logger.debug(f"Error while making a payment. User {user.id} already has an active subscription")
        raise HTTPException(
            status_code=409, detail="User already has active an subscription"
        )

    unpaid_order = await OrderRepository.get_unpaid_order(user.id)
    if unpaid_order:
        if unpaid_order.state == OrderState.PROCESSING:
            logger.debug(f"Error while making a payment. User {user.id} already has an order in process")
            raise HTTPException(
                status_code=409, detail="User already has an order in process"
            )

        if unpaid_order.state == OrderState.DRAFT:
            logger.debug(f"Error while making a payment. User {user.id} has a draft order")
            raise HTTPException(status_code=409, detail="User has a draft order")

    product = await ProductRepository.get_by_id(payment_info_in.product_id)
    if not product:
        logger.debug(f"Error while making a payment for user {user.id}. Product not found")
        raise HTTPException(status_code=404, detail="Product not found")

    logger.info(f"Making a payment order for user {user.id} with product {product.id}")
    async with in_transaction():
        subscription = await SubscriptionRepository.create(user.id, product.id)
        logger.debug(f"Subscription {subscription.id} created successfully for user {user.id}")

        order = await OrderRepository.create(
            user_id=user.id,
            product_id=product.id,
            user_email=payment_info_in.email,
            subscription_id=subscription.id,
            payment_system=payment_info_in.payment_system,
            amount=product.price,
            payment_currency_code=product.currency_code,
        )
        logger.debug(f"Order {order.id} created successfully for user {user.id}")

        payment_gateway = get_payment_gateway(payment_info_in.payment_system)
        payment = await payment_gateway.create_payment(order)

        logger.debug(f"Payment {payment.id} created successfully for user {user.id} using {payment_info_in.payment_system}")
        await OrderRepository.update(
            order.id, external_id=payment.id, state=payment.state
        )
        logger.debug(f"Order {order.id} updated state to {payment.state} and now has external id {payment.id}")

    return PaymentInfoOut(
        client_secret=payment.client_secret,
        payment_system=payment_info_in.payment_system,
    )


@user_router.get("/order/draft", response_model=PaymentInfoOut)
async def get_draft_order(
    user: AuthorizedUser = Depends(get_user),
):
    """ Draft order getting by user """
    if not user:
        logger.debug("Error while getting draft order. User is not authorized.")
        raise HTTPException(status_code=403, detail="Unauthorized user")

    unpaid_order = await OrderRepository.get_unpaid_order(user.id)
    if not unpaid_order:
        logger.debug(f"Error while getting draft order. User {user.id} has no unpaid orders.")
        raise HTTPException(status_code=404, detail="User has no unpaid orders")

    payment_gateway = get_payment_gateway(unpaid_order.payment_system)
    payment = await payment_gateway.get_payment(unpaid_order)

    logger.debug(f"Draft order returned successfully for user {user.id}.")
    return PaymentInfoOut(
        payment_system=unpaid_order.payment_system,
        client_secret=payment.client_secret,
    )


@user_router.get("/payment_methods", response_model=List[PaymentMethodOut])
async def get_payment_methods(
    user: AuthorizedUser = Depends(get_user),
):
    """ Payment methods getting by user """
    if not user:
        logger.debug("Error while trying to access payment methods. Unauthorized user.")
        raise HTTPException(status_code=403, detail="Unauthorized user")

    payment_methods: List[
        PaymentMethods
    ] = await PaymentMethodRepository.get_user_payment_methods(user.id)

    return parse_obj_as(List[PaymentMethodOut], payment_methods)


@user_router.get("/products", response_model=List[ProductOut], status_code=200)
async def get_products(
    user: AuthorizedUser = Depends(get_user),
):
    """ Products list getting by user """
    if not user:
        logger.debug("Error while trying to access products. Unauthorized user.")
        raise HTTPException(status_code=403, detail="Unauthorized user")

    products: List[Products] = await ProductRepository.get_active_products()
    return parse_obj_as(List[ProductOut], products)


@user_router.get("/subscription", response_model=SubscriptionOut, status_code=200)
async def get_subscription(
    user: AuthorizedUser = Depends(get_user),
):
    """ Subscription info getting by user """
    if not user:
        logger.debug("Error while trying to access subscription. Unauthorized user.")
        raise HTTPException(status_code=403, detail="Unauthorized user")

    subscription = await SubscriptionRepository.get_user_subscription(user.id)
    if not subscription:
        logger.debug(f"Error while trying to access subscription. User {user.id} has no active subscriptions.")
        raise HTTPException(status_code=404, detail="Active subscription not found")

    return parse_obj_as(SubscriptionOut, subscription)


@user_router.post("/subscription/cancel", status_code=200)
async def cancel_subscription(
    user: AuthorizedUser = Depends(get_user),
):
    """ Subscription cancelling by user """
    if not user:
        logger.debug("Error while trying to cancel subscription. Unauthorized user.")
        raise HTTPException(status_code=403, detail="Unauthorized user")

    subscription = await SubscriptionRepository.get_user_subscription(user.id)
    if not subscription:
        logger.debug(f"Error while trying to cancel subscription. User {user.id} has no active subscriptions.")
        raise HTTPException(
            status_code=404, detail="User has no active subscriptions"
        )

    await SubscriptionRepository.cancel(subscription.id)


@user_router.post("/subscription/refund", status_code=200)
async def refund_subscription(
    user: AuthorizedUser = Depends(get_user),
):
    """ Payment refunding by user """
    if not user:
        logger.debug("Error while trying to refund a subscription. Unauthorized user.")
        raise HTTPException(status_code=403, detail="Unauthorized user")

    subscription = await SubscriptionRepository.get_user_subscription(user.id)
    if not subscription:
        logger.debug(f"Error while trying to refund subscription. User {user.id} has no active subscriptions.")
        raise HTTPException(status_code=404, detail="Active subscription not found")

    order = await OrderRepository.get_subscription_order(user.id, subscription.id)
    if not order:
        logger.debug(f"Error while trying to refund subscription. User {user.id} has no paid orders.")
        raise HTTPException(status_code=404, detail="Paid order not found")

    refund_amount = calculate_refund_amount(
        subscription.end_date,
        order.payment_amount,
        order.product.period,
    )

    if not refund_amount:
        logger.debug(f"Error during the calculation of refund amount for the oder {order.id}.")
        raise HTTPException(status_code=400, detail="Subscription has ended")

    logger.info(f"Making a refund for user {user.id} / subscription {subscription.id} / {order.id}")
    async with in_transaction():
        refund_order = await OrderRepository.create_refund_order(order, refund_amount)

        payment_gateway = get_payment_gateway(refund_order.payment_system)
        refund = await payment_gateway.create_refund(refund_order)

        await OrderRepository.update(
            refund_order.id, external_id=refund.id, state=refund.state
        )
        logger.info(f"Successfully created a refund order {refund_order.id}")

        await SubscriptionRepository.to_deactivate(refund_order.subscription.id)
        # воркер будет проверять заказы (рефанды) со статусом пейд для таких подписок, и если он находит такой ордер,
        # то будет посылать запрос в биллинг апи на отмену этой подписки
        logger.info(f"Subscription {subscription.id} is going to be deactivated soon")

