"""Module with definition of `ProductRepository` class"""

from typing import List, Optional

from src.db.models import Products


class ProductRepository:
    """Class with operations on Products ORM models"""

    @staticmethod
    async def get_by_id(product_id: str) -> Optional[Products]:
        """
        Get product by primary key

        @param product_id: product identifier
        @return: class `Products` instance if it exists, otherwise, `None`
        """
        return await Products.get_or_none(pk=product_id)

    @staticmethod
    async def get_active_products() -> List[Products]:
        """
        Get all active products
        @return: list of class `Products` instances
        """
        return await Products.filter(active=True).all()
