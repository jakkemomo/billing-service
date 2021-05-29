"""Module with definition of `PaymentMethodRepository` class"""

from json import dumps
from typing import List, Optional
from uuid import uuid4

from src.db.models import PaymentMethods
from tortoise import timezone


class PaymentMethodRepository:
    """Class with operations on PaymentMethod ORM models"""

    @staticmethod
    async def get(payment_method_id: str) -> Optional[PaymentMethods]:
        """
        Get payment method by primary key

        @param payment_method_id: payment method identifier
        @return: class `PaymentMethods` instance if it exists, otherwise, `None`
        """
        return await PaymentMethods.get_or_none(pk=payment_method_id)

    @staticmethod
    async def get_default(user_id: str) -> Optional[PaymentMethods]:
        """
        Get user default payment method

        @param user_id: user identifier
        @return: class `PaymentMethods` instance if it exists, otherwise, `None`
        """
        return await PaymentMethods.filter(user_id=user_id, is_default=True).first()

    @staticmethod
    async def get_user_payment_methods(user_id: str) -> List[PaymentMethods]:
        """
        Get all user payment methods

        @param user_id: user identifier
        @return: list of class `PaymentMethods` instances
        """
        return await PaymentMethods.filter(user_id=user_id).all()

    @staticmethod
    async def create(
        user_id: str,
        external_id: str,
        payment_system: str,
        payment_type: str,
        data: dict = None,
    ) -> PaymentMethods:
        """
        Create new payment method

        @note: If payment method with the same `external_id` exists `is_default` field will be set to `True`
        @note: New created payment method will be consider as default
        @param user_id: user identifier
        @param external_id: payment method identifier in a payment system
        @param payment_system: payment system of payment method
        @param payment_type: type of payment method, e.g. `card`
        @param data: payment method information to display, it haven't to contain a critical data
        @return: class `PaymentMethods` instance of created payment method
        """
        pm = await PaymentMethods.get_or_none(external_id=external_id)
        if pm:
            await PaymentMethods.filter(
                user_id=user_id, external_id=external_id
            ).update(
                is_default=True,
                modified=timezone.now(),
            )
        else:
            pm = await PaymentMethods.create(
                id=uuid4(),
                user_id=user_id,
                external_id=external_id,
                payment_system=payment_system,
                type=payment_type,
                is_default=True,
                data=json.dumps(data),
                created=timezone.now(),
                modified=timezone.now(),
            )
        await PaymentMethods.filter(
            user_id=user_id, external_id__not=external_id
        ).update(
            is_default=False,
            modified=timezone.now(),
        )
        return pm
