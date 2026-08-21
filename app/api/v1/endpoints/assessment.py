import random
from fractions import Fraction
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


# One item per skill is a *screen*, not a measurement, so the scoring rule in
# submit_assessment is deliberately asymmetric: a miss includes the unit, a hit
# offers to skip it. Including a unit the student did not need is cheap;
# skipping one they did need is not.
QUESTIONS_PER_SKILL = {"quick": 1, "full": 3}
QUICK_MAX_QUESTIONS = 20
# Below this percentage on a tag, the unit is included in the study plan.
WEAK_THRESHOLD = 60


def _unit_tag(db: Session, unit: models.Unit) -> str | None:
    """The skill this unit assesses.

    `title` holds the skill for every seeded course. `description` is free text —
    matching on it alone meant no course ever produced a tag that matched a
    question, which left the diagnostic returning 404 for everything.
    """
    for candidate in (unit.title, unit.description):
        if not candidate:
            continue
        if _answerable(
            db.query(models.Question)
            .filter(
                models.Question.skill == candidate,
                models.Question.review_status == models.ReviewStatus.PUBLISHED,
            )
            .limit(60)
            .all()
        ):
            return candidate
    return None


def _answerable(questions: list[models.Question]) -> list[models.Question]:
    """Drop questions the runner cannot present.

    A question needs either choices to pick from or a fill-in box to type into.
    One with neither — a grid-in still typed as multiple choice — renders as a
    prompt with no answers and strands the student. Filtered in Python rather
    than SQL because JSON emptiness is spelled differently across backends.
    """
    return [
        q
        for q in questions
        if q.options or q.question_type == models.QuestionType.FILL_IN
    ]


def _normalise(value) -> str:
    """Compare grid-in answers forgivingly.

    A typed answer arrives as "5", " 5", "$5$" or "5.0" for the same number.
    Exact string equality would mark all but one wrong, so strip the LaTeX and
    whitespace, then compare numerically when both sides are numbers.
    """
    text = str(value if value is not None else "").strip()
    text = text.replace("$", "").replace(" ", "").replace(",", "")
    if text.endswith("."):
        text = text[:-1]
    return text.lower()


def answers_match(given, expected) -> bool:
    a, b = _normalise(given), _normalise(expected)
    if a == b:
        return True
    try:
        return float(Fraction(a)) == float(Fraction(b))
    except (ValueError, ZeroDivisionError):
        return False


def _sample_for_tag(db: Session, tag: str, count: int) -> list[models.Question]:
    """Prefer medium items — they discriminate best when you only get one shot."""
    base = db.query(models.Question).filter(
        models.Question.skill == tag,
        models.Question.review_status == models.ReviewStatus.PUBLISHED,
    )
    medium = _answerable(
        base.filter(models.Question.difficulty == models.Difficulty.MEDIUM).limit(60).all()
    )
    picked = random.sample(medium, min(count, len(medium)))
    if len(picked) < count:
        chosen = {q.id for q in picked}
        rest = [q for q in _answerable(base.limit(60).all()) if q.id not in chosen]
        picked += random.sample(rest, min(count - len(picked), len(rest)))
    return picked


@router.post(
    "/courses/{course_id}/assessment/start",
    response_model=schemas.AssessmentStartResponse,
)
def start_assessment(
    course_id: str,
    depth: str = "quick",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.AssessmentStartResponse:
    """Start a diagnostic for a course. One question per skill by default.

    depth=quick (default) screens every skill with a single medium item, capped at
    QUICK_MAX_QUESTIONS so the test stays inside the ten minutes the UI promises.
    depth=full asks three per skill, which is long but actually measures.
    """
    if depth not in QUESTIONS_PER_SKILL:
        raise HTTPException(status_code=422, detail="depth must be 'quick' or 'full'")

    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    units = (
        db.query(models.Unit)
        .filter(models.Unit.course_id == course_id)
        .order_by(models.Unit.order_index)
        .all()
    )
    if not units:
        raise HTTPException(status_code=404, detail="Course has no units")

    per_skill = QUESTIONS_PER_SKILL[depth]
    seen_tags: set[str] = set()
    questions: list[schemas.AssessmentQuestion] = []

    for unit in units:
        tag = _unit_tag(db, unit)
        if not tag or tag in seen_tags:
            continue
        seen_tags.add(tag)
        if depth == "quick" and len(questions) + per_skill > QUICK_MAX_QUESTIONS:
            break
        for q in _sample_for_tag(db, tag, per_skill):
            questions.append(
                schemas.AssessmentQuestion(
                    id=q.id,
                    prompt=q.prompt,
                    question_type=q.question_type.value if q.question_type else "multiple-choice",
                    options=q.options,
                    skill=q.skill,
                    difficulty=q.difficulty.value if q.difficulty else "medium",
                    unit_tag=tag,
                )
            )

    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for course units")

    return schemas.AssessmentStartResponse(
        assessment_id=f"asmt-{course_id}",
        course_id=course_id,
        questions=questions,
    )


@router.post("/courses/{course_id}/assessment/submit", response_model=schemas.AssessmentSubmitResponse)
def submit_assessment(
    course_id: str,
    payload: schemas.AssessmentSubmitRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.AssessmentSubmitResponse:
    """Score assessment answers by tag. Tags below WEAK_THRESHOLD are weak.

    At depth=quick a tag carries a single item, so this reduces to "missed it =>
    study that unit". That asymmetry is intentional; see QUESTIONS_PER_SKILL.
    """
    # Verify student exists and belongs to current user
    student = db.query(models.Student).filter(models.Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if str(student.owner_user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this student")

    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Score each answer against the correct answer in the database
    tag_counts: dict[str, dict] = {}
    for answer in payload.answers:
        tag = answer.unit_tag
        if tag not in tag_counts:
            tag_counts[tag] = {"correct": 0, "total": 0}

        question = db.query(models.Question).filter(models.Question.id == answer.question_id).first()
        is_correct = bool(question) and answers_match(answer.answer, question.correct_answer)
        if is_correct:
            tag_counts[tag]["correct"] += 1
        tag_counts[tag]["total"] += 1

    weak_tags = []
    strong_tags = []
    tag_results = []
    total_correct = 0
    total_questions = 0

    for tag, counts in tag_counts.items():
        percent = (counts["correct"] / counts["total"]) * 100 if counts["total"] > 0 else 0
        level = "weak" if percent < WEAK_THRESHOLD else "strong"
        if level == "weak":
            weak_tags.append(tag)
        else:
            strong_tags.append(tag)
        tag_results.append(schemas.TagResult(
            tag=tag,
            correct=counts["correct"],
            total=counts["total"],
            percent=round(percent, 1),
            level=level,
        ))
        total_correct += counts["correct"]
        total_questions += counts["total"]

    return schemas.AssessmentSubmitResponse(
        assessment_id=f"asmt-{course_id}",
        student_id=payload.student_id,
        course_id=course_id,
        weak_tags=weak_tags,
        strong_tags=strong_tags,
        tag_results=tag_results,
        total_correct=total_correct,
        total_questions=total_questions,
    )
