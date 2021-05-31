from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel, UUIDModel

SCHEMA = settings.DB_SCHEMA

NULL_BLANK = {"null": True, "blank": True}

NULL_BLANK_FALSE = {"null": False, "blank": False}


class OrderState(models.TextChoices):
    """ Модель статусов заказов """

    draft = "draft", _("Черновик")
    processing = "processing", _("В процессе")
    paid = "paid", _("Оплачен")
    error = "error", _("Ошибка")


class SubscriptionState(models.TextChoices):
    """ Модель статусов подписок """

    active = "active", _("Активна")
    pre_active = "pre_active", _("Оплачена")
    to_deactivate = "to_deactivate", _("Готовится к отключению")
    inactive = "inactive", _("Неактивна")
    cancelled = "cancelled", _("Отменена пользователем")


class Product(TimeStampedModel, UUIDModel):
    """ Модель продукта """

    name = models.CharField(
        _("название"),
        max_length=50,
        **NULL_BLANK_FALSE,
    )
    description = models.TextField(
        _("описание"),
        **NULL_BLANK,
    )
    role_id = models.UUIDField(
        verbose_name=_("роль"),
        **NULL_BLANK_FALSE,
    )
    price = models.DecimalField(
        verbose_name=_("цена"),
        max_digits=10,
        decimal_places=2,
        **NULL_BLANK_FALSE,
    )
    period = models.IntegerField(
        verbose_name=_("период"),
        **NULL_BLANK_FALSE,
    )
    active = models.BooleanField(
        verbose_name=_("активен"),
        default=False,
        **NULL_BLANK_FALSE,
    )
    currency_code = models.CharField(
        _("код валюты"),
        max_length=3,
        **NULL_BLANK_FALSE,
    )

    class Meta:
        verbose_name = _("продукт")
        verbose_name_plural = _("продукты")
        db_table = f'{SCHEMA}"."products'

    def __str__(self):
        return self.name


class Subscription(TimeStampedModel, UUIDModel):
    """ Модель пользовательской подписки """

    product = models.ForeignKey(
        Product,
        verbose_name=_("продукт"),
        related_name="subscription_product",
        on_delete=models.RESTRICT,
        **NULL_BLANK_FALSE,
    )
    user_id = models.UUIDField(
        verbose_name=_("пользователь"),
        **NULL_BLANK_FALSE,
    )
    start_date = models.DateField(
        verbose_name=_("дата начала"),
        **NULL_BLANK_FALSE,
    )
    end_date = models.DateField(
        verbose_name=_("дата окончания"),
        **NULL_BLANK_FALSE,
    )
    state = models.CharField(
        _("статус"),
        max_length=20,
        choices=SubscriptionState.choices,
        default=SubscriptionState.inactive,
        **NULL_BLANK_FALSE,
    )

    class Meta:
        verbose_name = _("подписка")
        verbose_name_plural = _("подписки")
        db_table = f'{SCHEMA}"."subscriptions'

    def __str__(self):
        return f"{self.product.name}/{self.user_id}"


class PaymentMethod(TimeStampedModel, UUIDModel):
    """ Модель метода оплаты """

    external_id = models.CharField(
        _("внешний идентификатор"),
        max_length=50,
        **NULL_BLANK_FALSE,
    )
    user_id = models.UUIDField(
        verbose_name=_("пользователь"),
        **NULL_BLANK_FALSE,
    )
    payment_system = models.CharField(
        _("платежная система"),
        max_length=50,
        **NULL_BLANK_FALSE,
    )
    type = models.CharField(
        _("тип"),
        max_length=50,
        **NULL_BLANK_FALSE,
    )
    is_default = models.BooleanField(
        verbose_name=_("по умолчанию"),
        default=False,
        **NULL_BLANK_FALSE,
    )
    data = models.JSONField(
        "информация для фронта",
        default=dict,
        **NULL_BLANK
    )

    class Meta:
        verbose_name = _("метод оплаты")
        verbose_name_plural = _("методы оплаты")
        db_table = f'{SCHEMA}"."payment_methods'

    def __str__(self):
        return f"{self.payment_system}/{self.user_id}"


class Order(TimeStampedModel, UUIDModel):
    """ Модель заказа """

    external_id = models.CharField(
        _("внешний идентификатор"),
        max_length=50,
        **NULL_BLANK,
    )
    user_id = models.UUIDField(
        verbose_name=_("пользователь"),
        **NULL_BLANK_FALSE,
    )
    user_email = models.CharField(
        max_length=35,
        **NULL_BLANK_FALSE,
    )
    product = models.ForeignKey(
        Product,
        verbose_name=_("продукт"),
        related_name="order_product",
        on_delete=models.RESTRICT,
        **NULL_BLANK_FALSE,
    )
    subscription = models.ForeignKey(
        Subscription,
        verbose_name=_("подписка"),
        related_name="order_product",
        on_delete=models.RESTRICT,
        **NULL_BLANK_FALSE,
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        verbose_name=_("способ оплаты"),
        related_name="order_payment_method",
        on_delete=models.RESTRICT,
        **NULL_BLANK_FALSE,
    )
    src_order = models.ForeignKey(
        "Order",
        verbose_name=_("оригинальный заказ"),
        related_name="order_to_order",
        on_delete=models.RESTRICT,
        **NULL_BLANK,
    )
    state = models.CharField(
        _("статус"),
        max_length=20,
        choices=OrderState.choices,
        default=OrderState.draft,
        **NULL_BLANK_FALSE,
    )
    payment_amount = models.DecimalField(
        verbose_name=_("цена"),
        max_digits=10,
        decimal_places=2,
        **NULL_BLANK_FALSE,
    )
    payment_currency_code = models.CharField(
        _("код валюты"),
        max_length=3,
        **NULL_BLANK_FALSE,
    )
    payment_system = models.CharField(
        _("платежная система"),
        max_length=50,
        **NULL_BLANK_FALSE,
    )
    is_automatic = models.BooleanField(
        verbose_name=_("автоматический"),
        default=False,
        **NULL_BLANK_FALSE,
    )
    is_refund = models.BooleanField(
        verbose_name=_("возврат"),
        default=False,
        **NULL_BLANK_FALSE,
    )

    class Meta:
        verbose_name = _("заказ")
        verbose_name_plural = _("заказы")
        db_table = f'{SCHEMA}"."orders'

    def __str__(self):
        return f"{self.id}/{self.product.name}"
