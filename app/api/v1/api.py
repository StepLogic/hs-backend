from fastapi import APIRouter

from app.api.v1.endpoints import courses, questions, results, students, lessons, reviews, review_progress, curriculum, audio_upload, progress

api_router = APIRouter()

api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(results.router, prefix="/results", tags=["results"])
api_router.include_router(results.answers_router, prefix="/answers", tags=["answers"])
api_router.include_router(lessons.router, prefix="/lessons", tags=["lessons"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(review_progress.router, prefix="/review-progress", tags=["review-progress"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
api_router.include_router(curriculum.router, prefix="/curriculum", tags=["curriculum"])
api_router.include_router(audio_upload.router, prefix="/audio-upload", tags=["audio-upload"])
