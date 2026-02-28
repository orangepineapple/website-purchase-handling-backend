from pydantic import BaseModel


# ── Request models ────────────────────────────────────────────────

class CreateIntentRequest(BaseModel):
    productId: str
    quantity: int = 1


# ── Response models ───────────────────────────────────────────────

class CreateIntentResponse(BaseModel):
    client_secret: str


class VerifyPaymentResponse(BaseModel):
    status: str
    paid: bool
    amount: int
    currency: str
    metadata: dict


class OrderRecord(BaseModel):
    id: int
    stripe_payment_id: str
    product_id: str
    product_name: str
    amount: int
    currency: str
    status: str
    customer_email: str | None
    created_at: str


class OrdersListResponse(BaseModel):
    total: int
    orders: list[OrderRecord]
