from fastapi import APIRouter

from app.api.v1.endpoints import courses, questions, results, students

api_router = APIRouter()

api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(results.router, prefix="/results", tags=["results"])
api_router.include_router(
    results.answers_router, prefix="/answers", tags=["answers"]
)
