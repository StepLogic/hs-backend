import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.api.deps import get_db, require_roles

router = APIRouter()

# No 0/O/1/I/L — these get read out over the phone and typed by hand.
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def normalize(code: Optional[str]) -> str:
    return (code or "").strip().upper().replace("-", "").replace(" ", "")


def claim(db: Session, code: Optional[str]) -> Optional[models.InviteCode]:
    """Mark an unused code as used, without committing — the caller commits it together
    with the account it creates, so a failed sign-up does not burn the code.

    A conditional UPDATE rather than read-then-write: two sign-ups racing on one code
    cannot both see it unused."""
    code = normalize(code)
    if not code:
        return None
    claimed = (
        db.query(models.InviteCode)
        .filter(models.InviteCode.code == code, models.InviteCode.used_at.is_(None))
        .update({models.InviteCode.used_at: datetime.utcnow()}, synchronize_session=False)
    )
    if not claimed:
        return None
    return db.query(models.InviteCode).filter(models.InviteCode.code == code).one()


@router.get("/", response_model=list[schemas.InviteCodeResponse])
def list_invite_codes(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_roles("admin")),
) -> list[models.InviteCode]:
    return (
        db.query(models.InviteCode)
        .options(joinedload(models.InviteCode.used_by))
        .order_by(models.InviteCode.created_at.desc())
        .all()
    )


@router.post("/", response_model=schemas.InviteCodeResponse, status_code=201)
def create_invite_code(
    body: schemas.InviteCodeCreate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_roles("admin")),
) -> models.InviteCode:
    # 10 chars of a 31-letter alphabet is ~50 bits: not guessable, still typeable.
    code = "".join(secrets.choice(_ALPHABET) for _ in range(10))
    row = models.InviteCode(code=code, note=(body.note or "").strip() or None)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{invite_id}")
def delete_invite_code(
    invite_id: str,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_roles("admin")),
) -> dict[str, bool]:
    row = db.query(models.InviteCode).filter(models.InviteCode.id == invite_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Invite code not found")
    # A used code is the record of who paid for which account — keep it.
    if row.used_at is not None:
        raise HTTPException(status_code=409, detail="This code has already been used")
    db.delete(row)
    db.commit()
    return {"ok": True}
