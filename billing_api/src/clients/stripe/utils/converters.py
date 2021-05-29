from decimal import Decimal

from src.clients.stripe.models import StripePaymentIntent
from src.clients.stripe.models import StripePaymentStatus, StripeChargeStatus
from src.models.common import OrderState


def convert_payment_state(payment_intent: StripePaymentIntent) -> OrderState:
    """
    Замечание: В процессе работы не рассматриваем состояние `requires_confirmation`, оно не используется
    при оплате в нашем случае.
    При оплате заказа клиентом, рассматриваются 4 случая:
    1. Клиент даже не начал оплату заказа (закрыл страницу с оплатой),
       оставляем заказ в состоянии DRAFT, чтобы в дальнейшем он мог
       заново его оплатить.
    2. Начал оплату и завис на каком-то месте, например, не ввел 3D-Secure
       и закрыл страницу оплаты, снова оставляем заказ в состоянии DRAFT.
    3. Оплатил, но оплата не прошла, тоже оставляем в DRAFT, в дальнейшем
       он может ввести данные другой карты.
    4. Оплатил, но оплата проходит долго (PENDING). В этом случае выставляем PROCESSING.
    """
    is_automatic = payment_intent.metadata.is_automatic
    pi_status = payment_intent.status
    charges = payment_intent.charges.data
    charge = charges[0] if charges else None
    charge_status = charge.status if charge else None
    charge_status_mapping = {
        StripeChargeStatus.FAILED: OrderState.ERROR,
        StripeChargeStatus.PENDING: OrderState.PROCESSING
    }
    pi_status_mapping = {
        StripePaymentStatus.SUCCEEDED: OrderState.PAID,
        StripePaymentStatus.PROCESSING: OrderState.PROCESSING,
        StripePaymentStatus.REQUIRES_ACTIONS: OrderState.DRAFT,
    }
    order_state = pi_status_mapping.get(pi_status)
    if order_state:
        return order_state
    # if pi_status == StripePaymentStatus.SUCCEEDED:
    #     return OrderState.PAID
    #
    # if pi_status == StripePaymentStatus.PROCESSING:
    #     return OrderState.PROCESSING
    #
    # if pi_status == StripePaymentStatus.REQUIRES_ACTIONS:
    #     return OrderState.DRAFT

    if is_automatic:
        if pi_status == StripePaymentStatus.REQUIRES_PAYMENT_METHOD:
            # В случае, когда платеж выполнялся автоматически, всегда будет `charge`
            status = charge_status_mapping.get(charge_status)
            if status:
                return status
            # if charge_status == StripeChargeStatus.FAILED:
            #     return OrderState.ERROR
            # elif charge_status == StripeChargeStatus.PENDING:
            #     return OrderState.PROCESSING
    else:
        if pi_status == StripePaymentStatus.REQUIRES_PAYMENT_METHOD:
            if charge:
                status = charge_status_mapping.get(charge_status)
                if status:
                    return status
                # if charge_status == StripeChargeStatus.FAILED:
                #     return OrderState.ERROR
                # elif charge_status == StripeChargeStatus.PENDING:
                #     return OrderState.PROCESSING
            else:
                return OrderState.DRAFT
        return OrderState.PROCESSING


def convert_refund_status(status: StripeChargeStatus) -> OrderState:
    """
    Отображение статуса возврата на статус заказа.

    Так как в процессе работы рассматриваем возврат как заказ, то необходимо выполнить
    отображение статуса возврата на статус заказа для корректного хранения в БД и дальнейшей
    проверки статуса возврата, если он не будет выполнен сразу.
    """
    mapping = {
        StripeChargeStatus.FAILED: OrderState.ERROR,
        StripeChargeStatus.PENDING: OrderState.PROCESSING,
        StripeChargeStatus.SUCCEEDED: OrderState.PAID,
    }
    return mapping[status]


def convert_to_int(price: Decimal) -> int:
    return int(price * 100)


def convert_to_decimal(price: int) -> Decimal:
    return Decimal(price / 100)
