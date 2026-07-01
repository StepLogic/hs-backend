from typing import Optional
import json
import urllib.request

from fastapi import APIRouter, Body, Depends, HTTPException, Query
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
# ── Source-agnostic course import ──────────────────────────────────
# The platform is course-agnostic: any course defined in the JSON format
# can be imported from a file, URL (B2, GitHub, S3), or inline body.

COURSE_JSON_FIELDS = {"course", "skill_taxonomies", "units", "assessment_questions"}


def _import_course_json(db: Session, data: dict) -> dict:
    """Import a full course definition from a JSON dict. Source-agnostic."""
    if not COURSE_JSON_FIELDS.issubset(data.keys()):
        raise HTTPException(
            status_code=422,
            detail=f"Missing required keys: {COURSE_JSON_FIELDS - set(data.keys())}",
        )

    c = data["course"]

    # Delete existing course with same title (idempotent re-import)
    existing = db.query(models.Course).filter(models.Course.title == c["title"]).first()
    if existing:
        for unit in db.query(models.Unit).filter(models.Unit.course_id == existing.id).all():
            for lesson in db.query(models.Lesson).filter(models.Lesson.unit_id == unit.id).all():
                db.query(models.LessonProgress).filter(models.LessonProgress.lesson_id == lesson.id).delete()
                db.delete(lesson)
            db.delete(unit)
        db.query(models.Enrollment).filter(models.Enrollment.course_id == existing.id).delete()
        db.delete(existing)
        db.commit()

    # Map subject string to enum — platform supports any subject
    subject_map = {
        "math": models.Subject.MATH,
        "english_language_arts": models.Subject.ENGLISH_LANGUAGE_ARTS,
        "ela": models.Subject.ENGLISH_LANGUAGE_ARTS,
        "science": models.Subject.SCIENCE,
        "social_studies": models.Subject.SOCIAL_STUDIES,
        "world_languages": models.Subject.WORLD_LANGUAGES,
        "test_prep": models.Subject.TEST_PREP,
        "college_readiness": models.Subject.COLLEGE_READINESS,
    }
    subject = subject_map.get(c.get("subject", "math"), models.Subject.MATH)

    course_type_map = {"core": models.CourseType.CORE, "test_prep": models.CourseType.TEST_PREP,
                       "college_readiness": models.CourseType.COLLEGE_READINESS}
    course_type = course_type_map.get(c.get("course_type", "core"), models.CourseType.CORE)

    # Create course
    course = models.Course(
        subject=subject,
        course_type=course_type,
        title=c["title"],
        short_title=c.get("short_title", c["title"][:20]),
        description=c["description"],
        icon=c.get("icon", "📚"),
        color=c.get("color", "#4f46e5"),
        price=c.get("price", 0),
        original_price=c.get("original_price"),
        skills=c.get("skills", []),
        grade_range=c.get("grade_range", "9-12"),
        lesson_count=0,
        student_count=0,
        rating=c.get("rating", 0.0),
        review_count=0,
        features=c.get("features", []),
        image_emoji=c.get("image_emoji", c.get("icon", "📚")),
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    # Create skill taxonomies
    for tax in data.get("skill_taxonomies", []):
        existing_tax = db.query(models.SkillTaxonomy).filter(
            models.SkillTaxonomy.subject == subject,
            models.SkillTaxonomy.skill == tax["skill"],
        ).first()
        if not existing_tax:
            db.add(models.SkillTaxonomy(
                subject=subject,
                skill=tax["skill"],
                description=tax.get("description"),
            ))
    db.commit()

    # Create units + lessons + quiz questions
    total_lessons = 0
    for u_idx, u in enumerate(data.get("units", [])):
        unit = models.Unit(
            course_id=course.id,
            title=u["title"],
            slug=u["slug"],
            order_index=u_idx,
            description=u.get("description", ""),
        )
        db.add(unit)
        db.commit()
        db.refresh(unit)

        unit_video = u.get("video", "")

        for l_idx, lesson_def in enumerate(u.get("lessons", [])):
            # Create quiz questions first
            quiz_q_ids = []
            for q_idx, quiz_q in enumerate(lesson_def.get("quiz", [])):
                diff = models.Difficulty.EASY if q_idx == 0 else models.Difficulty.MEDIUM
                quiz_q_obj = models.Question(
                    subject=subject,
                    grade_level=12,
                    question_type=models.QuestionType.MULTIPLE_CHOICE,
                    prompt=quiz_q["prompt"],
                    options=quiz_q["options"],
                    correct_answer=quiz_q["correct"],
                    skill=lesson_def["skills"][0] if lesson_def.get("skills") else "general",
                    explanation=quiz_q["explanation"],
                    difficulty=diff,
                    review_status=models.ReviewStatus.PUBLISHED,
                )
                db.add(quiz_q_obj)
                db.commit()
                db.refresh(quiz_q_obj)
                quiz_q_ids.append(quiz_q_obj.id)

            # Build content blocks: video + read-along + callout + quiz_embed
            content_blocks = []
            lesson_video = lesson_def.get("video", "")
            video_src = lesson_video if lesson_video else unit_video
            if video_src:
                content_blocks.append({
                    "type": "video",
                    "src": video_src,
                    "caption": f"Video lesson: {lesson_def['title']}",
                })
            if lesson_def.get("read_along"):
                content_blocks.append({
                    "type": "markdown",
                    "content": lesson_def["read_along"],
                })
            content_blocks.append({
                "type": "callout",
                "title": "Lesson Quiz",
                "content": "Complete the quiz below to test your understanding.",
            })
            if quiz_q_ids:
                content_blocks.append({
                    "type": "quiz_embed",
                    "question_id": quiz_q_ids[0],
                })

            lesson = models.Lesson(
                unit_id=unit.id,
                title=lesson_def["title"],
                slug=lesson_def["slug"],
                order_index=l_idx,
                content=lesson_def.get("read_along", ""),
                content_blocks=content_blocks,
                resources=[],
                objectives=[f"Master {lesson_def['title']}"],
                homework=[{"question_id": qid} for qid in quiz_q_ids],
                duration_min=15,
                skills=lesson_def.get("skills", []),
                review_status=models.ReviewStatus.PUBLISHED,
                difficulty=models.Difficulty(lesson_def.get("difficulty", "medium")),
            )
            db.add(lesson)
            db.commit()
            db.refresh(lesson)

            # Prerequisite: previous lesson in same unit
            if l_idx > 0:
                prev = db.query(models.Lesson).filter(
                    models.Lesson.unit_id == unit.id,
                    models.Lesson.order_index == l_idx - 1,
                ).first()
                if prev:
                    lesson.prerequisite_lesson_id = prev.id
                    db.commit()

            total_lessons += 1

    # Create assessment questions
    assessment_count = 0
    for aq in data.get("assessment_questions", []):
        diff = models.Difficulty(aq.get("difficulty", "medium"))
        db.add(models.Question(
            subject=subject,
            grade_level=12,
            question_type=models.QuestionType.MULTIPLE_CHOICE,
            prompt=aq["prompt"],
            options=aq["options"],
            correct_answer=aq["correct"],
            skill=aq["skill"],
            explanation=aq["explanation"],
            difficulty=diff,
            review_status=models.ReviewStatus.PUBLISHED,
        ))
        assessment_count += 1
    db.commit()

    # Update lesson count
    course.lesson_count = total_lessons
    db.commit()

    return {
        "ok": True,
        "course_id": course.id,
        "course_title": course.title,
        "units": len(data.get("units", [])),
        "lessons": total_lessons,
        "assessment_questions": assessment_count,
    }


@router.post("/import", response_model=dict)
def import_course(
    *, db: Session = Depends(get_db), data: dict = Body(...)
) -> dict:
    """Import a course from a JSON body. Source-agnostic — any course format works."""
    return _import_course_json(db, data)


@router.post("/import-url", response_model=dict)
def import_course_from_url(
    *, db: Session = Depends(get_db), url: str = Query(...)
) -> dict:
    """Fetch a course JSON from any URL (B2, GitHub, S3) and import it."""
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")
    return _import_course_json(db, data)
