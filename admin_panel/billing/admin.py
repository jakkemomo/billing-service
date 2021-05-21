from django.contrib import admin

from .models import Order, PaymentMethod, Product, Subscription


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Панель администрирования заказов.
    """

    list_display = ["product", "user_id"]
    fields = [
        "external_id",
        "product",
        "subscription",
        "payment_method",
        "user_id",
        "state",
        "payment_amount",
        "payment_currency_code",
        "is_refund",
        "src_order",
    ]
    list_filter = ("state",)
    search_fields = ("product", "created", "id", "state")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Панель администрирования продуктов.
    """

    list_display = ["name", "description", "price", "period"]
    fields = [
        "name",
        "description",
        "price",
        "currency_code",
        "role_id",
        "period",
        "active",
    ]
    search_fields = ["name"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """
    Панель администрирования подписок.
    """

    list_display = ["product", "user_id", "start_date", "end_date", "state"]
    fields = ["product", "user_id", "start_date", "end_date", "state"]
    search_fields = ["state"]
    list_filter = ("state",)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """
    Панель администрирования методов оплаты.
    """

    list_display = ["user_id", "payment_system", "type"]
    fields = ["external_id", "user_id", "payment_system", "type", "is_default", "data"]
    search_fields = ["payment_system"]
    list_filter = ("payment_system",)
