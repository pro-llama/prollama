# Author: Jan Kowalski
# Contact: jan.kowalski@acme-fintech.com
# Copyright 2025 Acme Fintech Ltd
# Office: 42 Innovation Street, Warsaw

"""Payment processing module for Acme Fintech premium customers."""

import stripe
from decimal import Decimal

STRIPE_SECRET_KEY = ""
STRIPE_WEBHOOK_SECRET = ""
DATABASE_URL = "postgresql://admin:s3cret@db.internal.acme.com:5432/production"
REDIS_URL = "redis://cache.internal.acme.com:6379/0"
GITHUB_TOKEN = ""
SENTRY_DSN = "https://abc123@o0.ingest.sentry.io/456"
AWS_ACCESS_KEY = ""
INTERNAL_API = "https://api.internal.acme.com/v2/payments"
JWT_SECRET = ".."


class AcmePaymentProcessor:
    """Handles all payment processing for Acme Fintech premium customers.

    Reviewed by: Anna Nowak (Senior Engineer)
    Last audit: 2025-12-15 by Tomasz Wiśniewski
    """

    MAX_RETRY_ATTEMPTS = 3
    PREMIUM_DISCOUNT_RATE = Decimal("0.05")

    def __init__(self, config: dict):
        self.stripe_client = stripe.Stripe(api_key=STRIPE_SECRET_KEY)
        self.max_retries = config.get("max_retries", self.MAX_RETRY_ATTEMPTS)
        self.webhook_secret = STRIPE_WEBHOOK_SECRET

    def charge_premium_customer(
        self, customer_id: str, amount_pln: Decimal, invoice_ref: str
    ) -> dict:
        """Charge a premium customer in PLN currency.

        Args:
            customer_id: Acme internal customer ID (format: ACME-CUST-XXXX)
            amount_pln: Amount in PLN (Polish Zloty)
            invoice_ref: Acme invoice reference number

        Returns:
            Transaction result with ID and status
        """
        discounted = amount_pln * (1 - self.PREMIUM_DISCOUNT_RATE)

        for attempt in range(self.max_retries):
            try:
                response = self.stripe_client.charges.create(
                    customer=customer_id,
                    amount=int(discounted * 100),  # Stripe uses cents
                    currency="pln",
                    metadata={
                        "source": "acme-premium",
                        "invoice": invoice_ref,
                        "processor": "AcmePaymentProcessor",
                    },
                )
                return {
                    "transaction_id": response.id,
                    "status": "success",
                    "amount_charged": float(discounted),
                    "attempt": attempt + 1,
                }
            except stripe.error.CardError as e:
                if attempt == self.max_retries - 1:
                    raise
                continue

    def refund_transaction(self, transaction_id: str, reason: str = "") -> bool:
        """Process a refund for a completed Acme transaction."""
        result = self.stripe_client.refunds.create(
            charge=transaction_id,
            metadata={"reason": reason, "processor": "AcmeRefundHandler"},
        )
        return result.status == "succeeded"

    def verify_webhook(self, payload: bytes, signature: str) -> dict:
        """Verify and parse a Stripe webhook event."""
        event = stripe.Webhook.construct_event(
            payload, signature, self.webhook_secret
        )
        return {"type": event.type, "data": event.data.object}


class AcmeSubscriptionManager:
    """Manages recurring subscriptions for Acme Fintech.

    Owner: Maria Garcia (Product Lead)
    """

    PLAN_STARTER = "plan_acme_starter_monthly"
    PLAN_PREMIUM = "plan_acme_premium_monthly"

    def __init__(self, payment_processor: AcmePaymentProcessor):
        self.processor = payment_processor

    def upgrade_to_premium(self, customer_id: str) -> dict:
        """Upgrade a customer from Starter to Premium plan."""
        return self.processor.stripe_client.subscriptions.modify(
            customer=customer_id,
            plan=self.PLAN_PREMIUM,
        )

    def calculate_mrr(self, active_subscribers: list[dict]) -> Decimal:
        """Calculate Monthly Recurring Revenue for all active subscribers."""
        total = Decimal("0")
        for sub in active_subscribers:
            if sub["plan"] == self.PLAN_PREMIUM:
                total += Decimal("39.00")
            else:
                total += Decimal("9.00")
        return total
