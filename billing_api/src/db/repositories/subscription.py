"""Module with definition of `SubscriptionRepository` class"""

from datetime import timedelta
from typing import Optional
from uuid import uuid4

from src.db.models import Subscriptions, SubscriptionState
from tortoise import timezone


class SubscriptionRepository:
    """Class with operations on Subscriptions ORM models"""

    @staticmethod
    async def get(subscription_id: str) -> Subscriptions:
        """
        Get subscription by primary key

        @param subscription_id: subscription identifier
        @return: class `Subscriptions` instance if subscription exists, otherwise, `None`
        """
        return await Subscriptions.get_or_none(pk=subscription_id).prefetch_related(
            "product"
        )

    @staticmethod
    async def get_user_subscription(user_id: str) -> Optional[Subscriptions]:
        """
        Get user subscription

        @note: returns only subscription with state `active` or `pre_active`
        @param user_id: user identifier
        @return: class `Subscriptions` instance if subscription exists, otherwise, `None`
        """
        return await Subscriptions.get_or_none(
            user_id=user_id,
            state__in=[SubscriptionState.ACTIVE, SubscriptionState.PRE_ACTIVE],
        ).prefetch_related("product")

    @staticmethod
    async def create(user_id: str, product_id: str) -> Subscriptions:
        """
        Create new subscription

        @note: subscription will have `inactive` state after creation
        @param user_id: user identifier
        @param product_id: product identifier
        @return: class `Subscriptions` instance of created subscription
        """
        now = timezone.now()
        return await Subscriptions.create(
            id=uuid4(),
            user_id=user_id,
            product_id=product_id,
            state=SubscriptionState.INACTIVE,
            start_date=now,
            end_date=now,
            created=now,
            modified=now,
        )

    @staticmethod
    async def activate(subscription_id: str, period: int):
        """
        Activate subscription

        @note: Method sets subscription state to `active` and extends subscription period
        @param subscription_id: subscription identifier
        @param period: number of days to extends subscription period
        """
        await Subscriptions.filter(pk=subscription_id).update(
            state=SubscriptionState.ACTIVE,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=period),
            modified=timezone.now(),
        )

    @staticmethod
    async def deactivate(subscription_id: str):
        """
        Deactivate subscription

        @note: Method sets subscription state to `inactive`
        @param subscription_id: subscription identifier
        """
        await Subscriptions.filter(pk=subscription_id).update(
            state=SubscriptionState.INACTIVE,
            modified=timezone.now(),
        )

    @staticmethod
    async def pre_activate(subscription_id: str):
        """
        Set subscription state to `pre_active`

        @param subscription_id: subscription identifier
        """
        await Subscriptions.filter(pk=subscription_id).update(
            state=SubscriptionState.PRE_ACTIVE,
            modified=timezone.now(),
        )

    @staticmethod
    async def to_deactivate(subscription_id: str):
        """
        Set subscription state to `to_deactivate`

        @param subscription_id: subscription identifier
        """
        await Subscriptions.filter(pk=subscription_id).update(
            state=SubscriptionState.TO_DEACTIVATE,
            modified=timezone.now(),
        )

    @staticmethod
    async def cancel(subscription_id: str):
        """
        Set subscription state to `cancelled`

        @param subscription_id: subscription identifier
        """
        await Subscriptions.filter(pk=subscription_id).update(
            state=SubscriptionState.CANCELLED,
            modified=timezone.now(),
        )
