"""Сервисные функции для взаимодействия с платежным API Stripe."""

import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_API_KEY


def create_stripe_product(product_name: str) -> dict:
    """Создает продукт в Stripe и возвращает JSON-ответ."""
    return stripe.Product.create(name=product_name)


def create_stripe_price(amount: float, product_id: str) -> dict:
    """Создает цену в Stripe (сумма переводится в копейки) и возвращает JSON-ответ."""
    return stripe.Price.create(
        currency='rub',
        unit_amount=int(amount * 100),
        product=product_id,
    )


def create_stripe_session(price_id: str) -> dict:
    """Создает платежную сессию в Stripe и возвращает JSON-ответ (включая id и url)."""
    return stripe.checkout.Session.create(
        success_url='http://127.0.0',
        line_items=[{'price': price_id, 'quantity': 1}],
        mode='payment',
    )


def retrieve_stripe_session(session_id: str) -> dict:
    """Получает актуальные данные о сессии оплаты из Stripe по её ID."""
    return stripe.checkout.Session.retrieve(session_id)
