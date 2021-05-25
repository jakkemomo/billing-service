from typing import List, Optional

from src.db.models import Products


class ProductRepository:
    @staticmethod
    async def get_by_id(product_id: str) -> Optional[Products]:
        return await Products.get_or_none(pk=product_id)

    @staticmethod
    async def get_active_products() -> List[Products]:
        return await Products.filter(active=True).all()
