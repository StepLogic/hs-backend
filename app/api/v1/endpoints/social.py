from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("/forum", response_model=list[schemas.ForumPostResponse])
def read_forum_posts(
    course_id: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.ForumPost]:
    return crud.get_forum_posts(db, course_id=course_id, skip=skip, limit=limit)


@router.post("/forum", response_model=schemas.ForumPostResponse, status_code=201)
def create_forum_post(
    post_in: schemas.ForumPostCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.ForumPost:
    return crud.create_forum_post(db, post_in)


@router.get("/forum/{post_id}", response_model=schemas.ForumPostResponse)
def read_forum_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.ForumPost:
    post = crud.get_forum_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
