import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Enum, JSON, Text
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
