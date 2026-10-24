import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from sqlalchemy import func

from app import ai_service, crud, models, schemas
from app.api.deps import get_db, get_current_user, owned_student

logger = logging.getLogger(__name__)
router = APIRouter()


def _scope_students_query(
    db: Session, current_user: models.User
):
    query = db.query(models.Student)
    if current_user.role == models.Role.STUDENT:
        query = query.filter(models.Student.owner_user_id == current_user.id)
    elif current_user.role == models.Role.PARENT:
        query = query.filter(models.Student.owner_user_id == current_user.id)
    # teacher/admin see all
    return query


@router.get("/", response_model=list[schemas.StudentResponse])
def read_students(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(get_current_user),
) -> list[models.Student]:
    return (
        _scope_students_query(db, current_user)
        .options(joinedload(models.Student.owner))  # login_method reads it for every row
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{student_id}", response_model=schemas.StudentResponse)
def read_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Student:
    student = crud.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    if current_user.role in (models.Role.STUDENT, models.Role.PARENT):
        if str(student.owner_user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")
    return student


@router.post("/", response_model=schemas.StudentResponse, status_code=201)
def create_student(
    *,
    db: Session = Depends(get_db),
    student_in: schemas.StudentCreate,
    current_user: models.User = Depends(get_current_user),
) -> models.Student:
    # Auto-set owner to current user if not provided
    payload = student_in.model_dump()
    payload["owner_user_id"] = str(current_user.id)
    db_student = models.Student(**payload)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@router.put("/{student_id}", response_model=schemas.StudentResponse)
def update_student(
    *,
    student_id: str,
    db: Session = Depends(get_db),
    student_in: schemas.StudentUpdate,
    current_user: models.User = Depends(get_current_user),
) -> models.Student:
    student = crud.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    if current_user.role in (models.Role.STUDENT, models.Role.PARENT):
        if str(student.owner_user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")
    updated = crud.update_student(db, student_id, student_in)
    if updated is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return updated


@router.delete("/{student_id}")
def delete_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict[str, bool]:
    student = crud.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    owned_student(db, student_id, current_user)
    success = crud.delete_student(db, student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"ok": True}


@router.get("/{student_id}/results", response_model=list[schemas.TestResultResponse])
def read_student_results(
    student_id: str,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(get_current_user),
) -> list[models.TestResult]:
    student = crud.get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    if current_user.role in (models.Role.STUDENT, models.Role.PARENT):
        if str(student.owner_user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")
    return crud.get_test_results(db, skip=skip, limit=limit, student_id=student_id)


def _study_tip_summary(db: Session, student_id: str) -> dict:
    """Skill names, scores and counts only: this is all the AI ever sees."""
    skills = (
        db.query(models.SkillMastery)
        .filter(models.SkillMastery.student_id == student_id)
        .order_by(models.SkillMastery.mastery_score, models.SkillMastery.skill)
        .all()
    )
    weakest = [s for s in skills[:3] if s.mastery_score < 70]
    strongest = [s for s in reversed(skills[3:])][:2]
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent = {"right": 0, "wrong": 0}
    rows = (
        db.query(models.UserAnswer.is_correct, func.count())
        .join(models.TestResult, models.UserAnswer.test_result_id == models.TestResult.id)
        .filter(models.TestResult.student_id == student_id, models.TestResult.created_at >= week_ago)
        .group_by(models.UserAnswer.is_correct)
        .all()
    )
    for ok, n in rows:
        recent["right" if ok else "wrong"] = n
    assessment = (
        db.query(models.TestResult)
        .filter(models.TestResult.student_id == student_id, models.TestResult.source == "assessment")
        .order_by(models.TestResult.created_at.desc())
        .first()
    )
    weak_skills: list[str] = []
    if assessment:
        qids = [a.question_id for a in assessment.user_answers if not a.is_correct]
        if qids:
            weak_skills = sorted(
                {s for (s,) in db.query(models.Question.skill).filter(models.Question.id.in_(qids)) if s}
            )
    return {
        "weakest": [{"skill": s.skill, "mastery": s.mastery_score} for s in weakest],
        "strongest": [{"skill": s.skill, "mastery": s.mastery_score} for s in strongest],
        "recent": recent,
        "assessment_weak_skills": weak_skills,
    }


@router.get("/{student_id}/study-tip")
async def read_study_tip(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict:
    """AI tip from the student's recent work; regenerated only when there is newer activity."""
    student = owned_student(db, student_id, current_user)
    latest = db.query(func.max(models.TestResult.created_at)).filter(
        models.TestResult.student_id == student_id
    ).scalar()
    if latest is None:
        return {"tip": None}
    stored = student.study_tip
    if stored and student.study_tip_at and student.study_tip_at >= latest:
        return {"tip": stored}
    summary = _study_tip_summary(db, student_id)
    db.close()  # release the pooled connection before the slow AI call
    try:
        tip = (await ai_service.generate_study_tip(summary)).strip()
    except Exception as e:
        logger.warning("study tip generation failed: %s", type(e).__name__)
        return {"tip": stored}
    if not tip:
        return {"tip": stored}
    db.query(models.Student).filter(models.Student.id == student_id).update(
        {"study_tip": tip, "study_tip_at": latest}
    )
    db.commit()
    return {"tip": tip}
