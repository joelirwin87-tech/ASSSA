"""Stripe payment helpers."""
from __future__ import annotations

from typing import Optional

import stripe

from app.config import StripeConfig


class PaymentError(RuntimeError):
    """Raised when Stripe checkout session creation fails."""


def init_stripe(config: StripeConfig) -> None:
    stripe.api_key = config.secret_key


def create_checkout_session(
    config: StripeConfig,
    customer_email: str,
    success_params: Optional[dict[str, str]] = None,
) -> str:
    success_url = config.success_url
    if success_params:
        query = "&".join(f"{key}={value}" for key, value in success_params.items())
        success_url = f"{success_url}?{query}"

    line_items = (
        [
            {
                "price": config.price_id,
                "quantity": 1,
            }
        ]
        if config.price_id
        else [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "Smart Contract Audit"},
                    "unit_amount": 9900,
                },
                "quantity": 1,
            }
        ]
    )

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=line_items,
            success_url=success_url,
            cancel_url=config.cancel_url,
            customer_email=customer_email,
            payment_intent_data={"metadata": {"product": "affordable-smart-contract-audit"}},
        )
    except Exception as exc:  # pragma: no cover - depends on network access
        raise PaymentError("Failed to create Stripe checkout session") from exc

    return session.url


def verify_payment(session_id: str) -> bool:
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as exc:  # pragma: no cover - depends on network access
        raise PaymentError("Unable to verify Stripe checkout session") from exc
    return bool(session.get("payment_status") == "paid")


__all__ = ["create_checkout_session", "init_stripe", "verify_payment", "PaymentError"]
