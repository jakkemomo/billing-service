import time

import psycopg2
import requests
import schedule

from scheduler.db import AbstractStorage, PostgresDB
from scheduler.settings import Settings, logger

settings = Settings()
SERVICE_URL = settings.get_service_url()


class Scheduler:
    def __init__(self, db: AbstractStorage):
        self.db = db

    def check_processing_orders(self):
        """ Get orders in state Draft, In progress and send them for update to Billing API """
        processing_orders = self.db.get_processing_orders()
        for order in processing_orders:
            self.send_order_for_update(order.id)
            time.sleep(settings.REQUEST_DELAY)

    def check_overdue_orders(self):
        """
        Get orders in state Draft, In progress that are not processed for more than 10 days and send them
        for cancelling to Billing API
        """
        overdue_orders = self.db.get_overdue_orders()
        for overdue_order in overdue_orders:
            self.send_order_for_cancel(overdue_order.id)
            time.sleep(settings.REQUEST_DELAY)

    def check_subscriptions(self):
        """
        Runner for gathering subscriptions once a day and
        sending requests to Billing API to update or cancel a subscription.
        """
        self.check_active_subscriptions()
        self.check_overdue_subscriptions()

    def check_active_subscriptions(self):
        """
        Get Active subscriptions which need to be repaid.
        Send them to Billing API for update.
        """
        subscriptions = self.db.get_active_subscriptions()
        for subscription in subscriptions:
            self.send_subscription_for_update(subscription.id)
            time.sleep(settings.REQUEST_DELAY)

    def check_overdue_subscriptions(self):
        """
        Get Active subscriptions which need to be cancelled.
        Send them to Billing API for deactivation.
        """
        overdue_subscriptions = self.db.get_overdue_subscriptions()
        for overdue_subscription in overdue_subscriptions:
            self.send_subscription_for_cancel(overdue_subscription.id)
            time.sleep(settings.REQUEST_DELAY)

    def check_pre_active_subscriptions(self):
        """
        Get Pre Active subscriptions which need to be Activated.
        Send them to Billing API for activation.
        """
        pre_active_subscriptions = self.db.get_pre_active_subscriptions()
        for pre_active_subscription in pre_active_subscriptions:
            self.send_order_for_activate(pre_active_subscription.id)
            time.sleep(settings.REQUEST_DELAY)

    def check_pre_deactivate_subscriptions(self):
        """
        Get Pre Deactivated subscriptions which need to be Deactivated.
        Send them to Billing API for deactivation.
        """
        pre_deactivate_subscriptions = self.db.get_pre_deactivate_subscriptions()
        for subscription in pre_deactivate_subscriptions:
            self.send_subscription_for_cancel(subscription.id)
            time.sleep(settings.REQUEST_DELAY)

    @staticmethod
    def send_subscription_for_update(subscription_id: str) -> None:
        """
        Send request for payment to Blling API
        :param subscription_id: UUID of subscription
        :return: None
        """
        try:
            logger.info(
                f"Sending request to Billing API to update a subscription with id {subscription_id}"
            )
            requests.post(
                f"{SERVICE_URL}/subscription/{subscription_id}/recurring_payment"
            )
        except Exception as e:
            logger.error(
                "Error while sending a request to update a subscription to Billing API: %s"
                % e
            )

    @staticmethod
    def send_order_for_activate(subscription_id: str) -> None:
        """
        Send request for activation of the subscription to the Blling API
        :param subscription_id: UUID of subscription
        :return: None
        """
        try:
            logger.info(
                f"Sending request to Billing API to activate a subscription with id {subscription_id}"
            )
            requests.post(f"{SERVICE_URL}/subscription/{subscription_id}/activate")

        except Exception as e:
            logger.error(
                "Error while sending a request to activate a subscription to Billing API: %s"
                % e
            )

    @staticmethod
    def send_subscription_for_cancel(subscription_id: str) -> None:
        """
        Send request for cancelling a user subscription to Blling API
        :param subscription_id: UUID of subscription
        :return: None
        """
        try:
            logger.info(
                f"Sending request to Billing API to cancel a subscription with id {subscription_id}"
            )
            requests.post(f"{SERVICE_URL}/subscription/{subscription_id}/deactivate")
        except Exception as e:
            logger.error(
                "Error while sending a request to cancel a subscription to Billing API: %s"
                % e
            )

    @staticmethod
    def send_order_for_update(order_id: str) -> None:
        """
        Send request for Blling API to update an order
        :param order_id: UUID of order
        :return: None
        """
        try:
            logger.info(
                f"Sending request to Billing API to update an order with id {order_id}"
            )
            requests.post(f"{SERVICE_URL}/order/{order_id}/update_info")
        except Exception as e:
            logger.error(
                f"Error while sending a request to update an order to Billing API: {e}"
            )

    @staticmethod
    def send_order_for_cancel(order_id: str) -> None:
        """
        Send request for Blling API to set an Error state on order
        :param order_id: UUID of order
        :return: None
        """
        try:
            logger.info(
                f"Sending request to Billing API to cancel an order with id {order_id}"
            )
            requests.post(f"{SERVICE_URL}/order/{order_id}/cancel")
        except Exception as e:
            logger.error(
                f"Error while sending a request to cancel an order to Billing API: {e}"
            )


if __name__ == "__main__":
    logger.info("Billing scheduler is starting")
    pg_connection = PostgresDB(
        psycopg2.connect(
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            options=f"-c search_path={settings.DB_SCHEMA}",
        )
    )
    scheduler = Scheduler(pg_connection)

    schedule.every().day.at("10:30").do(scheduler.check_subscriptions)
    schedule.every().day.at("10:30").do(scheduler.check_overdue_orders)
    schedule.every(5).seconds.do(scheduler.check_processing_orders)
    schedule.every(6).seconds.do(scheduler.check_pre_active_subscriptions)
    schedule.every(7).seconds.do(scheduler.check_pre_deactivate_subscriptions)

    logger.info("Billing scheduler is running")

    while True:
        schedule.run_pending()
        time.sleep(1)
