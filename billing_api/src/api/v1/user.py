from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import parse_obj_as
from src.clients import get_payment_gateway
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
        raise HTTPException(status_code=403, detail="Unauthorized user")

    subscription = await SubscriptionRepository.get_user_subscription(user.id)
    if subscription:
        raise HTTPException(
            status_code=409, detail="User already has active subscription"
        )

    unpaid_order = await OrderRepository.get_unpaid_order(user.id)
    if unpaid_order:
        if unpaid_order.state == OrderState.PROCESSING:
            raise HTTPException(
                status_code=409, detail="User already has a order in process"
            )

        if unpaid_order.state == OrderState.DRAFT:
            raise HTTPException(status_code=409, detail="User has a draft order")

    product = await ProductRepository.get_by_id(payment_info_in.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    async with in_transaction():
        subscription = await SubscriptionRepository.create(user.id, product.id)

        order = await OrderRepository.create(
            user_id=user.id,
            product_id=product.id,
            user_email=payment_info_in.email,
            subscription_id=subscription.id,
            payment_system=payment_info_in.payment_system,
            amount=product.price,
            payment_currency_code=product.currency_code,
        )

        payment_gateway = get_payment_gateway(payment_info_in.payment_system)
        payment = await payment_gateway.create_payment(order)

        await OrderRepository.update(
            order.id, external_id=payment.id, state=payment.state
        )

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
        raise HTTPException(status_code=403, detail="Unauthorized user")

    unpaid_order = await OrderRepository.get_unpaid_order(user.id)
    if not unpaid_order:
        raise HTTPException(status_code=404, detail="User has no unpaid orders")

    payment_gateway = get_payment_gateway(unpaid_order.payment_system)
    payment = await payment_gateway.get_payment(unpaid_order)

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
        raise HTTPException(status_code=403, detail="Unauthorized user")

    payment_methods: List[
        PaymentMethods
    ] = await PaymentMethodRepository.get_user_payment_methods(user.id)

    return parse_obj_as(List[PaymentMethodOut], payment_methods)


@user_router.get("/products", response_model=List[ProductOut])
async def get_products(
    user: AuthorizedUser = Depends(get_user),
):
    """ Products list getting by user """
    if not user:
        raise HTTPException(status_code=403, detail="Unauthorized user")

    products: List[Products] = await ProductRepository.get_active_products()
    return parse_obj_as(List[ProductOut], products)


@user_router.get("/subscription", response_model=SubscriptionOut)
async def get_subscription(
    user: AuthorizedUser = Depends(get_user),
):
    """ Subscription info getting by user """
    if not user:
        raise HTTPException(status_code=403, detail="Unauthorized user")

    subscription = await SubscriptionRepository.get_user_subscription(user.id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Active subscription not found")

    return parse_obj_as(SubscriptionOut, subscription)


@user_router.post("/subscription/cancel")
async def cancel_subscription(
    user: AuthorizedUser = Depends(get_user),
):
    """ Subscription cancelling by user """
    if not user:
        raise HTTPException(status_code=403, detail="Unauthorized user")

    subscription = await SubscriptionRepository.get_user_subscription(user.id)
    if subscription:
        raise HTTPException(
            status_code=404, detail="User has no active subscriptions"
        )

    await SubscriptionRepository.cancel(subscription.id)


@user_router.post("/subscription/refund")
async def refund_subscription(
    user: AuthorizedUser = Depends(get_user),
):
    """ Payment refunding by user """
    if not user:
        raise HTTPException(status_code=403, detail="Unauthorized user")

    subscription = await SubscriptionRepository.get_user_subscription(user.id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Active subscription not found")

    order = await OrderRepository.get_subscription_order(user.id, subscription.id)
    if not order:
        raise HTTPException(status_code=404, detail="Paid order not found")

    refund_amount = calculate_refund_amount(
        subscription.end_date,
        order.payment_amount,
        order.product.period,
    )

    if not refund_amount:
        raise HTTPException(status_code=400, detail="Subscription has ended")

    async with in_transaction():
        refund_order = await OrderRepository.create_refund_order(order, refund_amount)

        payment_gateway = get_payment_gateway(refund_order.payment_system)
        refund = await payment_gateway.create_refund(refund_order)

        await OrderRepository.update(
            refund_order.id, external_id=refund.id, state=refund.state
        )
