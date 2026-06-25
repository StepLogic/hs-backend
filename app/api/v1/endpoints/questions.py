from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db

router = APIRouter()


@router.get("/", response_model=list[schemas.QuestionResponse])
def read_questions(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    subject: Optional[str] = None,
    grade_level: Optional[int] = None,
    skill: Optional[str] = None,
    status: Optional[str] = Query(None),
) -> list[models.Question]:
    query = db.query(models.Question)
    if subject is not None:
        query = query.filter(models.Question.subject == subject)
    if grade_level is not None:
        query = query.filter(models.Question.grade_level == grade_level)
    if skill is not None:
        query = query.filter(models.Question.skill == skill)
    if status is not None:
        query = query.filter(models.Question.review_status == status)
    else:
        query = query.filter(models.Question.review_status == models.ReviewStatus.PUBLISHED)
    return query.offset(skip).limit(limit).all()


@router.get("/{question_id}", response_model=schemas.QuestionResponse)
def read_question(question_id: str, db: Session = Depends(get_db)) -> models.Question:
    question = crud.get_question(db, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post("/", response_model=schemas.QuestionResponse, status_code=201)
def create_question(
    *, db: Session = Depends(get_db), question_in: schemas.QuestionCreate
) -> models.Question:
    return crud.create_question(db, question_in)


@router.put("/{question_id}", response_model=schemas.QuestionResponse)
def update_question(
    *,
    question_id: str,
    db: Session = Depends(get_db),
    question_in: schemas.QuestionUpdate,
) -> models.Question:
    question = crud.update_question(db, question_id, question_in)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.delete("/{question_id}")
def delete_question(
    question_id: str, db: Session = Depends(get_db)
) -> dict[str, bool]:
    success = crud.delete_question(db, question_id)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"ok": True}
