from fastapi import APIRouter, HTTPException
from models.subscriber import SubscribeRequest, SubscribeResponse, SubscribersListResponse
from db import queries

# ================================================================
# SUBSCRIBERS ROUTER
# Mounted at /subscribers in main.py
# ================================================================

router = APIRouter()


@router.post("", response_model=SubscribeResponse)
def subscribe(data: SubscribeRequest):
    """Add a new email subscriber."""
    inserted = queries.insert_subscriber(
        email=data.email,
        name=data.name,
        source=data.source,
    )
    # Return success even if already subscribed — don't leak whether
    # an email exists in our database
    return SubscribeResponse(success=True, message="Thanks for subscribing!")


@router.get("", response_model=SubscribersListResponse)
def list_subscribers(limit: int = 100, offset: int = 0):
    """
    List all active subscribers.
    ⚠️  Protect this in production with an API key or remove it.
    """
    total, subscribers = queries.get_subscribers(limit=limit, offset=offset)
    return SubscribersListResponse(total=total, subscribers=subscribers)


@router.delete("/{email}", response_model=SubscribeResponse)
def unsubscribe(email: str):
    """Unsubscribe an email address (soft delete)."""
    found = queries.unsubscribe_email(email)
    if not found:
        raise HTTPException(status_code=404, detail="Email not found.")
    return SubscribeResponse(success=True, message="Unsubscribed successfully.")