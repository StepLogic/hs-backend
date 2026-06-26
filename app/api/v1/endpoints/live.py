from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user, require_roles

router = APIRouter()


@router.get("/", response_model=list[schemas.LiveSessionResponse])
def read_sessions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    course_id: str | None = None,
    status: str | None = None,
    current_user: models.User = Depends(get_current_user),
) -> list[models.LiveSession]:
    return crud.get_live_sessions(db, skip=skip, limit=limit, course_id=course_id, status=status)


@router.post("/", response_model=schemas.LiveSessionResponse, status_code=201)
def create_session(
    *,
    db: Session = Depends(get_db),
    session_in: schemas.LiveSessionCreate,
    _teacher: models.User = require_roles("teacher", "admin"),
) -> models.LiveSession:
    return crud.create_live_session(db, session_in)


@router.get("/{session_id}", response_model=schemas.LiveSessionResponse)
def read_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.LiveSession:
    session = crud.get_live_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/{session_id}", response_model=schemas.LiveSessionResponse)
def update_session(
    session_id: str,
    session_in: schemas.LiveSessionUpdate,
    db: Session = Depends(get_db),
    _teacher: models.User = require_roles("teacher", "admin"),
) -> models.LiveSession:
    session = crud.update_live_session(db, session_id, session_in)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    _admin: models.User = require_roles("admin"),
) -> None:
    deleted = crud.delete_live_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/start", response_model=schemas.LiveSessionResponse)
def start_session(
    session_id: str,
    db: Session = Depends(get_db),
    _teacher: models.User = require_roles("teacher", "admin"),
) -> models.LiveSession:
    session = crud.get_live_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        from app.video import create_room
        room = create_room(name=f"session-{session_id}", expiry_min=session.duration_min)
        session.meeting_url = room.get("url")
    except RuntimeError:
        # ponytail: Daily not configured — generate a placeholder URL for dev
        session.meeting_url = f"https://daily.co/dev-placeholder-{session_id}"
    session.status = models.LiveStatus.LIVE
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/end", response_model=schemas.LiveSessionResponse)
def end_session(
    session_id: str,
    db: Session = Depends(get_db),
    _teacher: models.User = require_roles("teacher", "admin"),
) -> models.LiveSession:
    session = crud.update_live_session(
        db, session_id, schemas.LiveSessionUpdate(status=models.LiveStatus.ENDED)
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/join", response_model=schemas.LiveSessionResponse)
def join_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.LiveSession:
    session = crud.get_live_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != models.LiveStatus.LIVE:
        raise HTTPException(status_code=400, detail="Session is not live")
    # ponytail: capacity check deferred; add when live attendance tracking implemented
    return session
