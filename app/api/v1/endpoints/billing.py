import os

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# ponytail: use env-based price IDs; fallback to test values
PRICE_IDS = {
    "monthly": os.getenv("STRIPE_PRICE_MONTHLY", "price_monthly"),
    "annual": os.getenv("STRIPE_PRICE_ANNUAL", "price_annual"),
    "lifetime": os.getenv("STRIPE_PRICE_LIFETIME", "price_lifetime"),
}


@router.post("/checkout")
def create_checkout(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    plan: str,
) -> dict:
    if plan not in PRICE_IDS:
        raise HTTPException(status_code=400, detail="Invalid plan")

    # Create or reuse Stripe customer
    existing = crud.get_subscription_by_user(db, str(current_user.id))
    customer_id = existing.stripe_customer_id if existing else None

    if not customer_id:
        customer = stripe.Customer.create(email=current_user.email)
        customer_id = customer.id
        # Persist customer ID for reuse
        if existing:
            existing.stripe_customer_id = customer_id
            db.commit()
        else:
            crud.create_subscription(
                db,
                schemas.SubscriptionCreate(
                    user_id=str(current_user.id),
                    plan=plan,
                    status="pending",
                    stripe_customer_id=customer_id,
                ),
            )

    success_url = os.getenv("STRIPE_SUCCESS_URL", "http://localhost:5173/billing?success=1")
    cancel_url = os.getenv("STRIPE_CANCEL_URL", "http://localhost:5173/billing?canceled=1")

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": PRICE_IDS[plan], "quantity": 1}],
        mode="subscription" if plan != "lifetime" else "payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return {"url": session.url}


@router.post("/webhook")
def stripe_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    payload = request.body()
    sig_header = request.headers.get("stripe-signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        customer_id = session_obj.get("customer")
        subscription_id = session_obj.get("subscription")

        sub = db.query(models.Subscription).filter(
            models.Subscription.stripe_customer_id == customer_id
        ).first()
        if sub:
            sub.stripe_subscription_id = subscription_id
            sub.status = "active"
            db.commit()

    elif event["type"] == "invoice.payment_failed":
        subscription_id = event["data"]["object"].get("subscription")
        sub = db.query(models.Subscription).filter(
            models.Subscription.stripe_subscription_id == subscription_id
        ).first()
        if sub:
            sub.status = "past_due"
            db.commit()

    return {"status": "ok"}


@router.get("/subscription")
def get_subscription(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.SubscriptionResponse | None:
    sub = crud.get_subscription_by_user(db, str(current_user.id))
    if not sub:
        return None
    return sub
