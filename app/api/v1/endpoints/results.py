from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db

router = APIRouter()
answers_router = APIRouter()


# ─── Test Results ───

@router.get("/", response_model=list[schemas.TestResultResponse])
def read_test_results(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    student_id: Optional[str] = None,
) -> list[models.TestResult]:
    return crud.get_test_results(db, skip=skip, limit=limit, student_id=student_id)


@router.get("/{result_id}", response_model=schemas.TestResultResponse)
def read_test_result(
    result_id: str, db: Session = Depends(get_db)
) -> models.TestResult:
    result = crud.get_test_result(db, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Test result not found")
    return result


@router.post("/", response_model=schemas.TestResultResponse, status_code=201)
def create_test_result(
    *, db: Session = Depends(get_db), result_in: schemas.TestResultCreate
) -> models.TestResult:
    return crud.create_test_result(db, result_in)


@router.put("/{result_id}", response_model=schemas.TestResultResponse)
def update_test_result(
    *,
    result_id: str,
    db: Session = Depends(get_db),
    result_in: schemas.TestResultUpdate,
) -> models.TestResult:
    result = crud.update_test_result(db, result_id, result_in)
    if result is None:
        raise HTTPException(status_code=404, detail="Test result not found")
    return result


@router.delete("/{result_id}")
def delete_test_result(
    result_id: str, db: Session = Depends(get_db)
) -> dict[str, bool]:
    success = crud.delete_test_result(db, result_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test result not found")
    return {"ok": True}


# ─── User Answers ───

@answers_router.get("/", response_model=list[schemas.UserAnswerResponse])
def read_user_answers(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    test_result_id: Optional[str] = None,
) -> list[models.UserAnswer]:
    return crud.get_user_answers(
        db, skip=skip, limit=limit, test_result_id=test_result_id
    )


@answers_router.get("/{answer_id}", response_model=schemas.UserAnswerResponse)
def read_user_answer(
    answer_id: str, db: Session = Depends(get_db)
) -> models.UserAnswer:
    answer = crud.get_user_answer(db, answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="User answer not found")
    return answer


@answers_router.post("/", response_model=schemas.UserAnswerResponse, status_code=201)
def create_user_answer(
    *, db: Session = Depends(get_db), answer_in: schemas.UserAnswerCreate
) -> models.UserAnswer:
    return crud.create_user_answer(db, answer_in)


@answers_router.put("/{answer_id}", response_model=schemas.UserAnswerResponse)
def update_user_answer(
    *,
    answer_id: str,
    db: Session = Depends(get_db),
    answer_in: schemas.UserAnswerUpdate,
) -> models.UserAnswer:
    answer = crud.update_user_answer(db, answer_id, answer_in)
    if answer is None:
        raise HTTPException(status_code=404, detail="User answer not found")
    return answer


@answers_router.delete("/{answer_id}")
def delete_user_answer(
    answer_id: str, db: Session = Depends(get_db)
) -> dict[str, bool]:
    success = crud.delete_user_answer(db, answer_id)
    if not success:
        raise HTTPException(status_code=404, detail="User answer not found")
    return {"ok": True}
