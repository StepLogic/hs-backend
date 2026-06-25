import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Enum, JSON, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Subject(str, PyEnum):
    MATH = "math"
    READING = "reading"
    COMPREHENSION = "comprehension"


class QuestionType(str, PyEnum):
    MULTIPLE_CHOICE = "multiple-choice"
    FILL_IN = "fill-in"
    ORDERING = "ordering"
    MATCHING = "matching"


class MasteryLevel(str, PyEnum):
    BEGINNER = "beginner"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    ADVANCED = "advanced"


class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subject = Column(Enum(Subject), nullable=False)
    grade_level = Column(Integer, nullable=False)
    question_type = Column("type", Enum(QuestionType), nullable=False)
    prompt = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    options = Column(JSON, nullable=True)
    pairs = Column(JSON, nullable=True)
    items = Column(JSON, nullable=True)
    correct_answer = Column("correct_answer", JSON, nullable=False)
    skill = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)
    hint = Column(Text, nullable=True)


class Course(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subject = Column(Enum(Subject), nullable=False)
    title = Column(String, nullable=False)
    short_title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String, nullable=False)
    color = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    skills = Column(JSON, nullable=False, default=list)
    grade_range = Column(String, nullable=False)
    lesson_count = Column(Integer, nullable=False, default=0)
    student_count = Column(Integer, nullable=False, default=0)
    rating = Column(Float, nullable=False, default=0.0)
    review_count = Column(Integer, nullable=False, default=0)
    features = Column(JSON, nullable=False, default=list)
    image_emoji = Column(String, nullable=False)


class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    grade_level = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    test_results = relationship("TestResult", back_populates="student", cascade="all, delete-orphan")


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    subject = Column(Enum(Subject), nullable=False)
    score = Column(Integer, nullable=False)
    grade_equivalent = Column(Integer, nullable=False)
    percentile = Column(Integer, nullable=False)
    correct_count = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    skill_breakdown = Column(JSON, nullable=False, default=dict)
    mastery_level = Column(Enum(MasteryLevel), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="test_results")
    user_answers = relationship("UserAnswer", back_populates="test_result", cascade="all, delete-orphan")


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    test_result_id = Column(String, ForeignKey("test_results.id"), nullable=False)
    question_id = Column(String, nullable=False)
    answer = Column(JSON, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    time_spent = Column(Integer, nullable=False)

    test_result = relationship("TestResult", back_populates="user_answers")


class Language(str, PyEnum):
    SPANISH = "spanish"


class ActivityType(str, PyEnum):
    LISTEN = "listen"
    CHOOSE = "choose"
    REPEAT = "repeat"
    ORDER = "order"
    DICTATION = "dictation"


class AudioAsset(Base):
    __tablename__ = "audio_assets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    language = Column(Enum(Language), nullable=False)
    text = Column(Text, nullable=False)
    voice = Column(String, nullable=False, default="ef_dora")
    speed = Column(Float, nullable=False, default=1.0)
    key = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("language", "text", "voice", "speed", name="uq_audio"),)


class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    language = Column(Enum(Language), nullable=False)
    unit = Column(String, nullable=False)
    unit_title = Column(String, nullable=False)
    title = Column(String, nullable=False)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    items = relationship("LessonItem", back_populates="lesson",
                         cascade="all, delete-orphan", order_by="LessonItem.order")


class LessonItem(Base):
    __tablename__ = "lesson_items"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id = Column(String, ForeignKey("lessons.id"), nullable=False)
    order = Column(Integer, nullable=False, default=0)
    type = Column(Enum(ActivityType), nullable=False)
    prompt = Column(Text, nullable=True)
    text = Column(Text, nullable=False)
    translation = Column(Text, nullable=True)
    audio_id = Column(String, ForeignKey("audio_assets.id"), nullable=True)
    audio_slow_id = Column(String, ForeignKey("audio_assets.id"), nullable=True)
    options = Column(JSON, nullable=True)
    items = Column(JSON, nullable=True)
    correct_answer = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    hint = Column(Text, nullable=True)
    lesson = relationship("Lesson", back_populates="items")
    audio = relationship("AudioAsset", foreign_keys=[audio_id])
    audio_slow = relationship("AudioAsset", foreign_keys=[audio_slow_id])


class UnitReview(Base):
    __tablename__ = "unit_reviews"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    language = Column(Enum(Language), nullable=False)
    unit = Column(String, nullable=False)
    unit_title = Column(String, nullable=False)
    poem_text = Column(Text, nullable=False)
    poem_audio_id = Column(String, ForeignKey("audio_assets.id"), nullable=True)
    questions = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("language", "unit"),)


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    lesson_id = Column(String, ForeignKey("lessons.id"), nullable=False)
    score = Column(Integer, nullable=False, default=0)
    completed = Column(Boolean, nullable=False, default=True)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("student_id", "lesson_id", name="uq_progress"),)


class ReviewProgress(Base):
    __tablename__ = "review_progress"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    review_id = Column(String, ForeignKey("unit_reviews.id"), nullable=False)
    score = Column(Integer, nullable=False, default=0)
    completed = Column(Boolean, nullable=False, default=True)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("student_id", "review_id", name="uq_review_progress"),)
