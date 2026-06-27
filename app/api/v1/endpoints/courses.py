from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db

router = APIRouter()


@router.get("/", response_model=list[schemas.CourseResponse])
def read_courses(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    subject: Optional[str] = None,
) -> list[models.Course]:
    return crud.get_courses(db, skip=skip, limit=limit, subject=subject)


@router.get("/{course_id}", response_model=schemas.CourseResponse)
def read_course(course_id: str, db: Session = Depends(get_db)) -> models.Course:
    course = crud.get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/", response_model=schemas.CourseResponse, status_code=201)
def create_course(
    *, db: Session = Depends(get_db), course_in: schemas.CourseCreate
) -> models.Course:
    return crud.create_course(db, course_in)


@router.put("/{course_id}", response_model=schemas.CourseResponse)
def update_course(
    *,
    course_id: str,
    db: Session = Depends(get_db),
    course_in: schemas.CourseUpdate,
) -> models.Course:
    course = crud.update_course(db, course_id, course_in)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.delete("/{course_id}")
def delete_course(course_id: str, db: Session = Depends(get_db)) -> dict[str, bool]:
    success = crud.delete_course(db, course_id)
    if not success:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"ok": True}

@router.delete("/all")
def delete_all_courses(db: Session = Depends(get_db)) -> dict:
    # ponytail: bulk delete — fine for admin reset, not for multi-tenant
    db.query(models.LessonProgress).delete()
    db.query(models.SkillMastery).delete()
    db.query(models.Enrollment).delete()
    db.query(models.Lesson).delete()
    db.query(models.Unit).delete()
    db.query(models.Question).delete()
    db.query(models.Course).delete()
    db.commit()
    return {"ok": True, "deleted": "all courses, units, lessons, questions, progress, enrollments, skill mastery"}
