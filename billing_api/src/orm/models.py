from typing import Tuple

from models.common import OrderState, SubscriptionState
from tortoise import fields
from tortoise.models import Model


class AbstractModel(Model):
    id = fields.UUIDField(pk=True)
    created = fields.DatetimeField()
    modified = fields.DatetimeField()

    class Meta:
        abstract = True


class PaymentMethods(AbstractModel):
    user_id = fields.UUIDField(null=False)
    external_id = fields.CharField(max_length=50, null=False)
    payment_system = fields.CharField(max_length=50, null=False)
    type = fields.CharField(max_length=50, null=False)
    is_default = fields.BooleanField(default=False, null=False)
    data = fields.JSONField(null=True)

    class Meta:
        table = "payment_methods"

    def __str__(self):
        return "PaymentMethod: %s -- %s -- %s" % (
            self.payment_system,
            self.type,
            self.data,
        )


class Products(AbstractModel):
    name = fields.CharField(max_length=255, null=False)
    description = fields.TextField()
    role_id = fields.UUIDField(null=False)
    price = fields.FloatField(null=False)
    currency_code = fields.CharField(max_length=3, null=False)
    period = fields.IntField(null=False)
    active = fields.BooleanField(default=False, null=False)

    class Meta:
        table = "products"

    def __str__(self):
        return "Product: %s -- %s %s" % (self.name, self.price, self.currency_code)

    def get_payment_price(self) -> Tuple[int, str]:
        return int(self.price * 100), str(self.currency_code)


class Subscriptions(AbstractModel):
    user_id = fields.UUIDField(null=False)
    product: fields.ForeignKeyRelation[Products] = fields.ForeignKeyField(
        "billing.Products", related_name="subscriptions", on_delete=fields.RESTRICT
    )
    start_date = fields.DateField(null=True)
    end_date = fields.DateField(null=True)
    state: SubscriptionState = fields.CharEnumField(
        SubscriptionState, default=SubscriptionState.INACTIVE
    )

    class Meta:
        table = "subscriptions"

    def __str__(self):
        return "Subscription: %s -- %s -- %s" % (self.user_id, self.product, self.state)


class Orders(AbstractModel):
    external_id = fields.CharField(max_length=50, null=True)
    user_id = fields.UUIDField(null=False)
    product: fields.ForeignKeyRelation[Products] = fields.ForeignKeyField(
        "billing.Products", related_name="orders", on_delete=fields.RESTRICT
    )
    subscription: fields.ForeignKeyRelation[Subscriptions] = fields.ForeignKeyField(
        "billing.Subscriptions", related_name="orders", on_delete=fields.RESTRICT
    )
    payment_system = fields.CharField(max_length=50, null=False)
    payment_method: fields.ForeignKeyRelation[PaymentMethods] = fields.ForeignKeyField(
        "billing.PaymentMethods",
        related_name="orders",
        on_delete=fields.RESTRICT,
        null=True,
    )
    payment_amount = fields.FloatField(null=False)
    payment_currency_code = fields.CharField(max_length=3, null=False)
    state: OrderState = fields.CharEnumField(OrderState, default=OrderState.DRAFT)
    is_refund = fields.BooleanField(default=False, null=False)
    src_order: fields.ForeignKeyRelation["Orders"] = fields.ForeignKeyField(
        "billing.Orders",
        related_name="refund",
        on_delete=fields.RESTRICT,
        null=True,
    )
    is_automatic = fields.BooleanField(default=False, null=False)
    user_email = fields.CharField(max_length=35, null=False)

    class Meta:
        table = "orders"

    def __str__(self):
        return "Order: %s -- %s -- %s -- %s %s" % (
            self.user_id,
            self.product,
            self.subscription,
            self.payment_amount,
            self.payment_currency_code,
        )
