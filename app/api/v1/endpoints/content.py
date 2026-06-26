from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, require_roles

router = APIRouter()


@router.post("/generate")
def generate_content(
    *,
    db: Session = Depends(get_db),
    _admin = Depends(require_roles("admin")),
    subject: str,
    grade_level: int,
    skill: str = "",
    topic: str = "",
    count: int = 5,
    difficulty: str = "medium",
    generate_lessons: bool = False,
) -> dict:
    """Generate draft content via LLM. Synchronous v1."""
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from seed_questions import generate_questions, generate_lesson

    results = {"questions": 0, "lessons": 0}

    if not generate_lessons:
        questions = generate_questions(
            subject=subject,
            grade_level=grade_level,
            skill=skill or subject,
            count=count,
            difficulty=difficulty,
            review_status="draft",
        )
        for q in questions:
            try:
                crud.create_question(db, schemas.QuestionCreate(**q))
                results["questions"] += 1
            except Exception:
                db.rollback()
        db.commit()
    else:
        lesson_data = generate_lesson(subject, topic or skill or subject, grade_level)
        # Create a dummy course/unit if none exist for the subject
        course = db.query(models.Course).filter(models.Course.subject == subject.upper() if hasattr(models.Subject, subject.upper()) else subject).first()
        if not course:
            # ponytail: create a minimal placeholder course for the generated lesson
            course = models.Course(
                subject=models.Subject(subject) if subject in [s.value for s in models.Subject] else models.Subject.MATH,
                title=f"{subject.title()} Grade {grade_level}",
                short_title=f"{subject.title()} {grade_level}",
                description="Auto-generated course placeholder.",
                icon="book",
                color="#3b82f6",
                price=0,
                grade_range=f"{grade_level}-{grade_level}",
                image_emoji="📚",
                skills=[skill or subject],
                features=["Auto-generated"],
            )
            db.add(course)
            db.flush()

        unit = db.query(models.Unit).filter(models.Unit.course_id == course.id).first()
        if not unit:
            unit = models.Unit(
                course_id=course.id,
                title="Unit 1",
                slug="unit-1",
                order_index=0,
                description="Auto-generated unit.",
            )
            db.add(unit)
            db.flush()

        lesson = models.Lesson(
            unit_id=unit.id,
            title=lesson_data["title"],
            slug=lesson_data["title"].lower().replace(" ", "-")[:50],
            content=lesson_data["content"],
            skills=lesson_data["skills"],
            review_status=models.ReviewStatus.DRAFT,
        )
        db.add(lesson)
        db.commit()
        results["lessons"] = 1

    return results
