from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict

from app.models import Subject, QuestionType, MasteryLevel


# ─── Question schemas ───
class QuestionBase(BaseModel):
    subject: Subject
    grade_level: int
    question_type: QuestionType
    prompt: str
    context: Optional[str] = None
    options: Optional[list[str]] = None
    pairs: Optional[list[dict[str, str]]] = None
    items: Optional[list[str]] = None
    correct_answer: Any
    skill: str
    explanation: str
    hint: Optional[str] = None


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    subject: Optional[Subject] = None
    grade_level: Optional[int] = None
    question_type: Optional[QuestionType] = None
    prompt: Optional[str] = None
    context: Optional[str] = None
    options: Optional[list[str]] = None
    pairs: Optional[list[dict[str, str]]] = None
    items: Optional[list[str]] = None
    correct_answer: Optional[Any] = None
    skill: Optional[str] = None
    explanation: Optional[str] = None
    hint: Optional[str] = None


class QuestionResponse(QuestionBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# ─── Course schemas ───
class CourseBase(BaseModel):
    subject: Subject
    title: str
    short_title: str
    description: str
    icon: str
    color: str
    price: float
    original_price: Optional[float] = None
    skills: list[str]
    grade_range: str
    lesson_count: int = 0
    student_count: int = 0
    rating: float = 0.0
    review_count: int = 0
    features: list[str]
    image_emoji: str


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    subject: Optional[Subject] = None
    title: Optional[str] = None
    short_title: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    skills: Optional[list[str]] = None
    grade_range: Optional[str] = None
    lesson_count: Optional[int] = None
    student_count: Optional[int] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    features: Optional[list[str]] = None
    image_emoji: Optional[str] = None


class CourseResponse(CourseBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# ─── Student schemas ───
class StudentBase(BaseModel):
    name: str
    email: Optional[str] = None
    grade_level: int


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    grade_level: Optional[int] = None


class StudentResponse(StudentBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── TestResult schemas ───
class TestResultBase(BaseModel):
    student_id: str
    subject: Subject
    score: int
    grade_equivalent: int
    percentile: int
    correct_count: int
    total_questions: int
    skill_breakdown: dict[str, Any]
    mastery_level: MasteryLevel


class TestResultCreate(TestResultBase):
    pass


class TestResultUpdate(BaseModel):
    student_id: Optional[str] = None
    subject: Optional[Subject] = None
    score: Optional[int] = None
    grade_equivalent: Optional[int] = None
    percentile: Optional[int] = None
    correct_count: Optional[int] = None
    total_questions: Optional[int] = None
    skill_breakdown: Optional[dict[str, Any]] = None
    mastery_level: Optional[MasteryLevel] = None


class TestResultResponse(TestResultBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── UserAnswer schemas ───
class UserAnswerBase(BaseModel):
    test_result_id: str
    question_id: str
    answer: Any
    is_correct: bool
    time_spent: int


class UserAnswerCreate(UserAnswerBase):
    pass


class UserAnswerUpdate(BaseModel):
    test_result_id: Optional[str] = None
    question_id: Optional[str] = None
    answer: Optional[Any] = None
    is_correct: Optional[bool] = None
    time_spent: Optional[int] = None


class UserAnswerResponse(UserAnswerBase):
    id: str
    model_config = ConfigDict(from_attributes=True)
