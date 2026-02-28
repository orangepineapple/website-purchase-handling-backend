import stripe
from fastapi import APIRouter, HTTPException, Request, Header
from config import settings
from models.payment import (
    CreateIntentRequest,
    CreateIntentResponse,
    VerifyPaymentResponse,
    OrdersListResponse,
)
from db import queries

# ================================================================
# PAYMENTS ROUTER
# Mounted at /payments in main.py
# ================================================================

router = APIRouter()

# Set Stripe secret key from config
stripe.api_key = settings.stripe_secret_key

# ================================================================
# PRODUCTS
# Prices are defined SERVER-SIDE only — never trust the frontend
# to tell you how much to charge.
# ================================================================

PRODUCTS = {
    "prod_starter": {"name": "Starter Pack", "price": 2999, "currency": "usd"},
    "prod_pro":     {"name": "Pro Pack",     "price": 7999, "currency": "usd"},
}


@router.post("/create-intent", response_model=CreateIntentResponse)
def create_payment_intent(data: CreateIntentRequest):
    """
    Creates a Stripe PaymentIntent and returns the client_secret.
    The client_secret is safe to pass to the frontend — it cannot
    be used to charge a card, only to confirm payment.
    """
    product = PRODUCTS.get(data.productId)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe is not configured.")

    try:
        intent = stripe.PaymentIntent.create(
            amount=product["price"] * data.quantity,
            currency=product["currency"],
            automatic_payment_methods={"enabled": True},
            metadata={
                "product_id": data.productId,
                "product_name": product["name"],
                "quantity": data.quantity,
            },
        )
        return CreateIntentResponse(client_secret=intent.client_secret)

    except stripe.StripeError as e:
        raise HTTPException(status_code=400, detail=e.user_message)


@router.get("/verify", response_model=VerifyPaymentResponse)
def verify_payment(payment_intent: str):
    """
    Verify a PaymentIntent status server-side.
    Call this from your success page before delivering the product.
    """
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent)
        return VerifyPaymentResponse(
            status=intent.status,
            paid=intent.status == "succeeded",
            amount=intent.amount,
            currency=intent.currency,
            metadata=dict(intent.metadata),
        )
    except stripe.StripeError as e:
        raise HTTPException(status_code=400, detail=e.user_message)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
):
    """
    Stripe sends signed events here when payments complete.
    ⚠️  Always verify the signature — without this anyone could
    POST a fake payment_intent.succeeded event.

    Setup in Stripe Dashboard → Developers → Webhooks:
      Endpoint URL: https://yourapi.com/payments/webhook
      Events to listen for:
        - payment_intent.succeeded
        - payment_intent.payment_failed
    """
    payload = await request.body()

    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured.")

    # Verify the webhook came from Stripe
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    # ── Handle events ─────────────────────────────────────────────
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]

        # Save the order to the database
        queries.insert_order(
            stripe_payment_id=intent["id"],
            product_id=intent["metadata"].get("product_id", ""),
            product_name=intent["metadata"].get("product_name", ""),
            amount=intent["amount"],
            currency=intent["currency"],
            status="succeeded",
            customer_email=intent.get("receipt_email"),
        )

        # ── TODO: Fulfil the order here ──────────────────────────
        # e.g. send confirmation email, grant access, etc.
        print(f"[stripe] Payment succeeded: {intent['id']}")

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        queries.update_order_status(intent["id"], "failed")
        print(f"[stripe] Payment failed: {intent['id']}")

    # Must return 200 — Stripe will retry if it gets anything else
    return {"received": True}


@router.get("/orders", response_model=OrdersListResponse)
def list_orders(limit: int = 100, offset: int = 0):
    """
    List all orders.
    ⚠️  Protect this in production with an API key.
    """
    total, orders = queries.get_orders(limit=limit, offset=offset)
    return OrdersListResponse(total=total, orders=orders)
