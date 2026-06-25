from datetime import datetime
from typing import Optional, Any

from sqlalchemy.orm import Session

from app import models, schemas


# ─── Questions ───

def get_question(db: Session, question_id: str) -> Optional[models.Question]:
    return db.query(models.Question).filter(models.Question.id == question_id).first()


def get_questions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    subject: Optional[str] = None,
    grade_level: Optional[int] = None,
) -> list[models.Question]:
    query = db.query(models.Question)
    if subject:
        query = query.filter(models.Question.subject == subject)
    if grade_level is not None:
        query = query.filter(models.Question.grade_level == grade_level)
    return query.offset(skip).limit(limit).all()


def create_question(db: Session, question: schemas.QuestionCreate) -> models.Question:
    db_question = models.Question(**question.model_dump())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def update_question(
    db: Session, question_id: str, question: schemas.QuestionUpdate
) -> Optional[models.Question]:
    db_question = get_question(db, question_id)
    if not db_question:
        return None
    update_data = question.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_question, key, value)
    db.commit()
    db.refresh(db_question)
    return db_question


def delete_question(db: Session, question_id: str) -> bool:
    db_question = get_question(db, question_id)
    if not db_question:
        return False
    db.delete(db_question)
    db.commit()
    return True


# ─── Courses ───

def get_course(db: Session, course_id: str) -> Optional[models.Course]:
    return db.query(models.Course).filter(models.Course.id == course_id).first()


def get_courses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    subject: Optional[str] = None,
) -> list[models.Course]:
    query = db.query(models.Course)
    if subject:
        query = query.filter(models.Course.subject == subject)
    return query.offset(skip).limit(limit).all()


def create_course(db: Session, course: schemas.CourseCreate) -> models.Course:
    db_course = models.Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


def update_course(
    db: Session, course_id: str, course: schemas.CourseUpdate
) -> Optional[models.Course]:
    db_course = get_course(db, course_id)
    if not db_course:
        return None
    update_data = course.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_course, key, value)
    db.commit()
    db.refresh(db_course)
    return db_course


def delete_course(db: Session, course_id: str) -> bool:
    db_course = get_course(db, course_id)
    if not db_course:
        return False
    db.delete(db_course)
    db.commit()
    return True


# ─── Students ───

def get_student(db: Session, student_id: str) -> Optional[models.Student]:
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def get_students(
    db: Session, skip: int = 0, limit: int = 100
) -> list[models.Student]:
    return db.query(models.Student).offset(skip).limit(limit).all()


def create_student(db: Session, student: schemas.StudentCreate) -> models.Student:
    db_student = models.Student(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def update_student(
    db: Session, student_id: str, student: schemas.StudentUpdate
) -> Optional[models.Student]:
    db_student = get_student(db, student_id)
    if not db_student:
        return None
    update_data = student.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_student, key, value)
    db.commit()
    db.refresh(db_student)
    return db_student


def delete_student(db: Session, student_id: str) -> bool:
    db_student = get_student(db, student_id)
    if not db_student:
        return False
    db.delete(db_student)
    db.commit()
    return True


# ─── Test Results ───

def get_test_result(db: Session, test_result_id: str) -> Optional[models.TestResult]:
    return db.query(models.TestResult).filter(models.TestResult.id == test_result_id).first()


def get_test_results(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[str] = None,
) -> list[models.TestResult]:
    query = db.query(models.TestResult)
    if student_id:
        query = query.filter(models.TestResult.student_id == student_id)
    return query.offset(skip).limit(limit).all()


def create_test_result(
    db: Session, test_result: schemas.TestResultCreate
) -> models.TestResult:
    db_test_result = models.TestResult(**test_result.model_dump())
    db.add(db_test_result)
    db.commit()
    db.refresh(db_test_result)
    return db_test_result


def update_test_result(
    db: Session, test_result_id: str, test_result: schemas.TestResultUpdate
) -> Optional[models.TestResult]:
    db_test_result = get_test_result(db, test_result_id)
    if not db_test_result:
        return None
    update_data = test_result.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_test_result, key, value)
    db.commit()
    db.refresh(db_test_result)
    return db_test_result


def delete_test_result(db: Session, test_result_id: str) -> bool:
    db_test_result = get_test_result(db, test_result_id)
    if not db_test_result:
        return False
    db.delete(db_test_result)
    db.commit()
    return True


# ─── User Answers ───

def get_user_answer(db: Session, user_answer_id: str) -> Optional[models.UserAnswer]:
    return db.query(models.UserAnswer).filter(models.UserAnswer.id == user_answer_id).first()


def get_user_answers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    test_result_id: Optional[str] = None,
) -> list[models.UserAnswer]:
    query = db.query(models.UserAnswer)
    if test_result_id:
        query = query.filter(models.UserAnswer.test_result_id == test_result_id)
    return query.offset(skip).limit(limit).all()


def create_user_answer(
    db: Session, user_answer: schemas.UserAnswerCreate
) -> models.UserAnswer:
    db_user_answer = models.UserAnswer(**user_answer.model_dump())
    db.add(db_user_answer)
    db.commit()
    db.refresh(db_user_answer)
    return db_user_answer


def update_user_answer(
    db: Session, user_answer_id: str, user_answer: schemas.UserAnswerUpdate
) -> Optional[models.UserAnswer]:
    db_user_answer = get_user_answer(db, user_answer_id)
    if not db_user_answer:
        return None
    update_data = user_answer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user_answer, key, value)
    db.commit()
    db.refresh(db_user_answer)
    return db_user_answer


def delete_user_answer(db: Session, user_answer_id: str) -> bool:
    db_user_answer = get_user_answer(db, user_answer_id)
    if not db_user_answer:
        return False
    db.delete(db_user_answer)
    db.commit()
    return True


# ─── Audio Assets ───

def get_audio_asset(db: Session, audio_id: str) -> Optional[models.AudioAsset]:
    return db.query(models.AudioAsset).filter(models.AudioAsset.id == audio_id).first()


def upsert_audio_asset(db: Session, language: str, text: str, voice: str, speed: float, key: str) -> models.AudioAsset:
    existing = db.query(models.AudioAsset).filter(
        models.AudioAsset.language == language,
        models.AudioAsset.text == text,
        models.AudioAsset.voice == voice,
        models.AudioAsset.speed == speed,
    ).first()
    if existing:
        existing.key = key
        db.commit()
        db.refresh(existing)
        return existing
    db_asset = models.AudioAsset(
        language=models.Language(language),
        text=text,
        voice=voice,
        speed=speed,
        key=key,
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset


# ─── Lessons ───

def get_lesson(db: Session, lesson_id: str) -> Optional[models.Lesson]:
    return db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()


def get_lessons(db: Session, language: Optional[str] = None) -> list[models.Lesson]:
    query = db.query(models.Lesson)
    if language:
        query = query.filter(models.Lesson.language == language)
    return query.order_by(models.Lesson.unit, models.Lesson.order).all()


def create_lesson(db: Session, language: str, unit: str, unit_title: str, title: str, order: int) -> models.Lesson:
    db_lesson = models.Lesson(
        language=models.Language(language),
        unit=unit,
        unit_title=unit_title,
        title=title,
        order=order,
    )
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson


def upsert_lesson(db: Session, language: str, unit: str, unit_title: str, title: str, order: int) -> models.Lesson:
    existing = db.query(models.Lesson).filter(
        models.Lesson.language == language,
        models.Lesson.unit == unit,
        models.Lesson.title == title,
    ).first()
    if existing:
        existing.unit_title = unit_title
        existing.order = order
        db.commit()
        db.refresh(existing)
        return existing
    return create_lesson(db, language, unit, unit_title, title, order)


# ─── Lesson Items ───

def create_lesson_item(db: Session, lesson_id: str, order: int, type_: str, text: str,
                       prompt: Optional[str] = None, translation: Optional[str] = None,
                       audio_id: Optional[str] = None, audio_slow_id: Optional[str] = None,
                       options: Optional[Any] = None, items: Optional[Any] = None,
                       correct_answer: Optional[Any] = None, explanation: Optional[str] = None,
                       hint: Optional[str] = None) -> models.LessonItem:
    db_item = models.LessonItem(
        lesson_id=lesson_id,
        order=order,
        type=models.ActivityType(type_),
        prompt=prompt,
        text=text,
        translation=translation,
        audio_id=audio_id,
        audio_slow_id=audio_slow_id,
        options=options,
        items=items,
        correct_answer=correct_answer,
        explanation=explanation,
        hint=hint,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_lesson_items(db: Session, lesson_id: str) -> list[models.LessonItem]:
    return db.query(models.LessonItem).filter(models.LessonItem.lesson_id == lesson_id).order_by(models.LessonItem.order).all()


# ─── Unit Reviews ───

def get_unit_review(db: Session, language: str, unit: str) -> Optional[models.UnitReview]:
    return db.query(models.UnitReview).filter(
        models.UnitReview.language == language,
        models.UnitReview.unit == unit,
    ).first()


def upsert_unit_review(db: Session, language: str, unit: str, unit_title: str,
                       poem_text: str, questions: Any,
                       poem_audio_id: Optional[str] = None) -> models.UnitReview:
    existing = db.query(models.UnitReview).filter(
        models.UnitReview.language == language,
        models.UnitReview.unit == unit,
    ).first()
    if existing:
        existing.unit_title = unit_title
        existing.poem_text = poem_text
        existing.questions = questions
        if poem_audio_id is not None:
            existing.poem_audio_id = poem_audio_id
        db.commit()
        db.refresh(existing)
        return existing
    db_review = models.UnitReview(
        language=models.Language(language),
        unit=unit,
        unit_title=unit_title,
        poem_text=poem_text,
        questions=questions,
        poem_audio_id=poem_audio_id,
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


# ─── Lesson Progress ───

def get_lesson_progress(db: Session, student_id: str) -> list[models.LessonProgress]:
    return db.query(models.LessonProgress).filter(models.LessonProgress.student_id == student_id).all()


def upsert_lesson_progress(db: Session, student_id: str, lesson_id: str, score: int, completed: bool = True) -> models.LessonProgress:
    existing = db.query(models.LessonProgress).filter(
        models.LessonProgress.student_id == student_id,
        models.LessonProgress.lesson_id == lesson_id,
    ).first()
    if existing:
        existing.score = score
        existing.completed = completed
        existing.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    db_progress = models.LessonProgress(
        student_id=student_id,
        lesson_id=lesson_id,
        score=score,
        completed=completed,
    )
    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return db_progress


# ─── Review Progress ───

def get_review_progress(db: Session, student_id: str) -> list[models.ReviewProgress]:
    return db.query(models.ReviewProgress).filter(models.ReviewProgress.student_id == student_id).all()


def upsert_review_progress(db: Session, student_id: str, review_id: str, score: int, completed: bool = True) -> models.ReviewProgress:
    existing = db.query(models.ReviewProgress).filter(
        models.ReviewProgress.student_id == student_id,
        models.ReviewProgress.review_id == review_id,
    ).first()
    if existing:
        existing.score = score
        existing.completed = completed
        existing.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    db_progress = models.ReviewProgress(
        student_id=student_id,
        review_id=review_id,
        score=score,
        completed=completed,
    )
    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return db_progress
