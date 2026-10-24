from datetime import date

from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.srs import score_to_quality, update_mastery


def record_answers(
    db: Session,
    student_id: str,
    subject: models.Subject,
    answers: list[schemas.PracticeAnswer],
    source: str | None,
    lesson_id: str | None = None,
) -> dict:
    """Re-grade against the bank, then write TestResult, UserAnswers, SkillMastery and
    (with a lesson_id) LessonProgress. Callers check ownership first."""
    # circular: assessment imports this module
    from app.api.v1.endpoints.assessment import answers_match

    # Grade against the bank rather than trusting the client's is_correct: the client
    # compared option text to a letter key and marked nearly every right answer wrong.
    for ans in answers:
        q = crud.get_question(db, ans.question_id)
        if q is not None:
            ans.is_correct = answers_match(ans.answer, q.correct_answer)

    # Write user answers and compute scores
    correct_count = sum(1 for a in answers if a.is_correct)
    total = len(answers)
    score = int((correct_count / total) * 100) if total else 0

    # Determine mastery level from score
    if score >= 90:
        mastery_level = models.MasteryLevel.ADVANCED
    elif score >= 70:
        mastery_level = models.MasteryLevel.PROFICIENT
    elif score >= 50:
        mastery_level = models.MasteryLevel.DEVELOPING
    else:
        mastery_level = models.MasteryLevel.BEGINNER

    # Create TestResult
    test_result_in = schemas.TestResultCreate(
        student_id=student_id,
        subject=subject,
        score=score,
        grade_equivalent=0,  # ponytail: simplified for adaptive practice
        percentile=0,
        correct_count=correct_count,
        total_questions=total,
        skill_breakdown={},
        mastery_level=mastery_level,
        source=source,
    )
    test_result = crud.create_test_result(db, test_result_in)

    # Write UserAnswers and update SkillMastery
    skill_masteries = []
    for ans in answers:
        ua = schemas.UserAnswerCreate(
            test_result_id=test_result.id,
            question_id=ans.question_id,
            answer=ans.answer,
            is_correct=ans.is_correct,
            time_spent=ans.time_spent,
            used_hint=ans.used_hint,
        )
        crud.create_user_answer(db, ua)

        q = crud.get_question(db, ans.question_id)
        if not q:
            continue
        q_subject = q.subject.value if hasattr(q.subject, "value") else q.subject
        sm = crud.get_skill_mastery_by_student_skill(
            db, student_id, q_subject, q.skill
        )
        if not sm:
            sm = crud.create_or_update_skill_mastery(
                db,
                schemas.SkillMasteryCreate(
                    student_id=student_id,
                    subject=q.subject,
                    skill=q.skill,
                    due_date=date.today(),
                ),
            )
        quality = score_to_quality(ans.is_correct, ans.time_spent, q.difficulty.value if hasattr(q.difficulty, "value") else q.difficulty)
        update_mastery(sm, quality)
        db.commit()
        db.refresh(sm)
        skill_masteries.append(sm)

    # Update lesson progress if lesson_id provided
    lesson_progress = None
    if lesson_id and skill_masteries:
        avg_mastery = int(sum(sm.mastery_score for sm in skill_masteries) / len(skill_masteries))
        progress_status = (
            models.LessonProgressStatus.COMPLETED
            if avg_mastery >= 70
            else models.LessonProgressStatus.IN_PROGRESS
        )
        lesson_progress = crud.create_or_update_lesson_progress(
            db,
            schemas.LessonProgressCreate(
                student_id=student_id,
                lesson_id=lesson_id,
                status=progress_status,
                mastery_score=avg_mastery,
            ),
        )

    return {
        "test_result": test_result,
        "skill_mastery": skill_masteries,
        "lesson_progress": lesson_progress,
    }
