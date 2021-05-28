from abc import ABC, abstractmethod
from typing import List

from psycopg2.extras import NamedTupleCursor


class AbstractStorage(ABC):
    def __init__(self, connection, *args, **kwargs):
        self.connection = connection

    @abstractmethod
    def get(self, query: str, *args, **kwargs) -> List:
        pass

    @abstractmethod
    def get_active_subscriptions(self, *args, **kwargs) -> List:
        pass

    @abstractmethod
    def get_pre_active_subscriptions(self, *args, **kwargs) -> List:
        pass

    @abstractmethod
    def get_pre_deactivate_subscriptions(self, *args, **kwargs) -> List:
        pass

    @abstractmethod
    def get_overdue_subscriptions(self, *args, **kwargs) -> List:
        pass

    @abstractmethod
    def get_processing_orders(self, *args, **kwargs) -> List:
        pass

    @abstractmethod
    def get_overdue_orders(self, *args, **kwargs) -> List:
        pass


class PostgresDB(AbstractStorage):
    def __init__(self, connection):
        super(PostgresDB, self).__init__(connection)

    def get(self, query: str, *args, **kwargs) -> List:
        with self.connection.cursor(cursor_factory=NamedTupleCursor) as cr:
            cr.execute(query)
            results = cr.fetchall()
            return results

    def get_active_subscriptions(self, *args, **kwargs) -> List:
        """
        Filter subscription by state=Active and end_date<Current Date, also check if there were 3 or more failed
        automatic payments for this subscription and if there are 3 of them - dont select this subscription.
        :return: List of Named Tuple Subscriptions
        """
        return self.get(
            """
        SELECT id FROM subscriptions s WHERE s.state='active' AND s.end_date<=current_date AND (s.id NOT IN
        (SELECT subscription_id FROM orders o WHERE (o.state='error' AND o.created>(current_date - INTERVAL '3 day')
        AND o.is_automatic=TRUE) GROUP BY subscription_id HAVING count(*)>=3))
        """
        )

    def get_pre_active_subscriptions(self, *args, **kwargs) -> List:
        """
        Select pre active subscriptions for activation.
        :return: List of Named Tuple Subscriptions
        """
        return self.get(
            """
            SELECT id FROM subscriptions s WHERE s.state='pre_active';
            """
        )

    def get_pre_deactivate_subscriptions(self, *args, **kwargs) -> List:
        """
        Select pre active subscriptions for activation.
        :return: List of Named Tuple Subscriptions
        """
        return self.get(
            """
            SELECT id FROM subscriptions s WHERE s.state='to_deactivate';
            """
        )

    def get_overdue_subscriptions(self, *args, **kwargs) -> List:
        """
        Filter subscription by state=Active and end_date<Current Date, also check if there were 3 or more failed
        automatic payments for this subscription and if there are 3 of them - select this subscriptions. Also check
        for cancelled overdue subscriptions and select them.
        :return: List of Named Tuple Subscriptions
        """
        return self.get(
            """
        SELECT id FROM subscriptions s WHERE (s.state='active' AND s.end_date<=current_date AND
        (s.id IN (SELECT subscription_id FROM orders o WHERE
        (o.state='error' AND o.created>(current_date - INTERVAL '3 day')::date AND o.is_automatic=TRUE)
        GROUP BY subscription_id HAVING count(*)>=3) )) or s.state='cancelled' AND s.end_date<=current_date
        """
        )

    def get_processing_orders(self, *args, **kwargs) -> List:
        return self.get(
            "SELECT id FROM orders WHERE state='processing' or state='draft';"
        )

    def get_overdue_orders(self, *args, **kwargs) -> List:
        return self.get(
            "SELECT id FROM orders WHERE state='draft' AND modified<now()-INTERVAL '10 days';"
        )
