import abc
from distutils.util import strtobool

from src.clients.stripe.models import StripePaymentStatus, StripeChargeStatus
from src.models.common import OrderState


class AbcPMDExtractor(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def extract(data: dict) -> dict:
        pass


class CardDataExtractor(AbcPMDExtractor):
    @staticmethod
    def extract(data: dict) -> dict:
        return {
            'brand': data['brand'],
            'exp_month': data['exp_month'],
            'exp_year': data['exp_year'],
            'last4': data['last4'],
        }


def get_pmd_extractor(pm_type: str) -> AbcPMDExtractor:
    if pm_type == 'card':
        return CardDataExtractor()
    else:
        raise ValueError()


def str_to_bool(value: str) -> bool:
    return bool(strtobool(value))


def extract_payment_state(data: dict) -> OrderState:
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
    is_automatic = str_to_bool(data['metadata']['is_automatic'])
    pi_status = StripePaymentStatus(data['status'])
    charges = data['charges']['data']
    charge = charges[0] if charges else None
    charge_status = StripeChargeStatus(charge['status']) if charge else None

    if pi_status == StripePaymentStatus.SUCCEEDED:
        return OrderState.PAID

    if pi_status == StripePaymentStatus.PROCESSING:
        return OrderState.PROCESSING

    if pi_status == StripePaymentStatus.REQUIRES_ACTIONS:
        return OrderState.DRAFT

    if is_automatic:
        if pi_status == StripePaymentStatus.REQUIRES_PAYMENT_METHOD:
            # В случае, когда платеж выполнялся автоматически, всегда будет `charge`
            if charge_status == StripeChargeStatus.FAILED:
                return OrderState.ERROR
            elif charge_status == StripeChargeStatus.PENDING:
                return OrderState.PROCESSING
    else:
        if pi_status == StripePaymentStatus.REQUIRES_PAYMENT_METHOD:
            if charge:
                if charge_status == StripeChargeStatus.FAILED:
                    return OrderState.DRAFT
                elif charge_status == StripeChargeStatus.PENDING:
                    return OrderState.PROCESSING
            else:
                return OrderState.DRAFT
        return OrderState.PROCESSING


def map_refund_status(status: StripeChargeStatus) -> OrderState:
    """Отображение статуса возврата на статус заказа.

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
