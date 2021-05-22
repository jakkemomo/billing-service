from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import parse_obj_as
from src.models.api import (
    PaymentInfoIn,
    PaymentInfoOut,
    PaymentMethodOut,
    ProductOut,
    SubscriptionOut,
)
from src.models.common import OrderState, SubscriptionState
from src.orm.models import PaymentMethods, Products
from src.repositories.order import OrderRepository
from src.repositories.payment_method import PaymentMethodRepository
from src.repositories.product import ProductRepository
from src.repositories.subscription import SubscriptionRepository
from src.services.payment_gateway import (
    PaymentGatewayService,
    get_payment_gateway_service,
)
from src.services.roles import RolesService, get_roles_service
from src.utils.auth import AuthorizedUser, get_user
from src.utils.refund import calculate_refund_amount

user_router = APIRouter()


@user_router.get("/user/subscription", response_model=SubscriptionOut)
async def get_subscription(
    user: AuthorizedUser = Depends(get_user),
):
    if not user:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized user",
        )

    subscription = await SubscriptionRepository.get_user_subscription(user.id)
    if not subscription:
        raise HTTPException(
            status_code=404,
            detail="Active subscription not found",
        )

    return SubscriptionOut(
        product_name=subscription.product.name,
        start_date=subscription.start_date.isoformat(),
        end_date=subscription.end_date.isoformat(),
    )


@user_router.post("/user/payment", response_model=PaymentInfoOut)
async def create_payment(
    payment_info_in: PaymentInfoIn,
    user: AuthorizedUser = Depends(get_user),
):
    """ Payment creating by user """
    if not user:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized user",
        )

    if await SubscriptionRepository.has_user_active_subscription(user.id):
        raise HTTPException(
            status_code=409,
            detail="User already has active subscription",
        )

    # Если из предыдущей сессии остался неоплаченный заказ, то возвращаем ифнормацию по нему
    unpaid_order = await OrderRepository.get_unpaid_order(user.id)
    if unpaid_order:
        if unpaid_order.state == OrderState.PROCESSING:
            raise HTTPException(
                status_code=409,
                detail="User already has processing order",
            )
        if unpaid_order.state == OrderState.DRAFT:
            payment_service: PaymentGatewayService = await get_payment_gateway_service(
                unpaid_order
            )
            payment = await payment_service.get_order()
            return PaymentInfoOut(
                client_secret=payment.client_secret,
                payment_system=unpaid_order.payment_system,
                is_new=False,
            )

    product = await ProductRepository.get_by_id(payment_info_in.product_id)

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

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

    payment_service: PaymentGatewayService = await get_payment_gateway_service(order)
    payment = await payment_service.create_service_payment()

    await OrderRepository.update(order.id, external_id=payment.id, state=payment.state)

    return PaymentInfoOut(
        client_secret=payment.client_secret,
        payment_system=payment_info_in.payment_system,
        is_new=True,
    )


@user_router.delete("/user/subscription/{subscription_id}")
async def cancel_subscription(
    subscription_id: str,
    user: AuthorizedUser = Depends(get_user),
):
    """ Subscription cancelling by user """
    if not user:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized user",
        )

    await SubscriptionRepository.deactivate(
        subscription_id,
        SubscriptionState.CANCELLED,
    )


@user_router.get("/user/payment_method", response_model=List[PaymentMethodOut])
async def get_payment_methods(
    user: AuthorizedUser = Depends(get_user),
):
    """ Payment methods getting by user """
    if not user:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized user",
        )

    payment_methods: List[
        PaymentMethods
    ] = await PaymentMethodRepository.get_user_payment_methods(user.id)

    return parse_obj_as(List[PaymentMethodOut], payment_methods)


@user_router.get("/user/product", response_model=List[ProductOut])
async def get_products(
    user: AuthorizedUser = Depends(get_user),
):
    """ Products list getting by user """
    if not user:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized user",
        )

    products: List[Products] = await ProductRepository.get_active_products()
    return parse_obj_as(List[ProductOut], products)


@user_router.post("/user/subscription/{subscription_id}/refund")
async def refund_payment(
    subscription_id: str,
    roles_service: RolesService = Depends(get_roles_service),
    user: AuthorizedUser = Depends(get_user),
):
    """ Payment refunding by user """
    if not user:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized user",
        )

    if not await SubscriptionRepository.has_user_active_subscription(user.id):
        raise HTTPException(
            status_code=404,
            detail="Active subscription not found",
        )

    order = await OrderRepository.get_subscription_order(user.id, subscription_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Paid order not found",
        )

    refund_amount = calculate_refund_amount(
        order.subscription.end_date,
        order.payment_amount,
        order.product.period,
    )

    if not refund_amount:
        raise HTTPException(
            status_code=400,
            detail=f"You cannot refund a subscription that ended at {order.subscription.end_date}",
        )

    refund_order = await OrderRepository.create(
        user_id=user.id,
        product_id=order.product.id,
        subscription_id=order.subscription.id,
        payment_method_id=order.payment_method_id,
        payment_system=order.payment_system,
        amount=refund_amount,
        payment_currency_code=order.product.currency_code,
        user_email=order.user_email,
        src_order=order,
        is_refund=True,
    )

    payment_service: PaymentGatewayService = await get_payment_gateway_service(
        refund_order
    )
    refund = await payment_service.create_service_refund()

    await OrderRepository.update(
        refund_order.id, external_id=refund.id, state=refund.state
    )

    if refund.state == OrderState.PAID:
        await SubscriptionRepository.deactivate(
            subscription_id, SubscriptionState.INACTIVE
        )
        await roles_service.revoke_role(user.id, order.product.role_id)
