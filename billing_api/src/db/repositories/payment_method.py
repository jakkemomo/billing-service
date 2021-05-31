from typing import List, Optional
from uuid import uuid4

from src.db.models import PaymentMethods
from tortoise import timezone


class PaymentMethodRepository:
    @staticmethod
    async def get(_id: str) -> Optional[PaymentMethods]:
        return await PaymentMethods.get_or_none(pk=_id)

    @staticmethod
    async def get_default(user_id: str) -> PaymentMethods:
        return await PaymentMethods.filter(user_id=user_id, is_default=True).first()

    @staticmethod
    async def get_user_payment_methods(user_id: str) -> List[PaymentMethods]:
        return await PaymentMethods.filter(user_id=user_id).all()

    @staticmethod
    async def create(
        user_id: str,
        external_id: str,
        payment_system: str,
        payment_type: str,
        data: dict = None,
    ) -> PaymentMethods:
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
                data=data,
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
