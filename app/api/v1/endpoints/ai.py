"""AI personalization endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import ai_service

router = APIRouter()


class PlanGenerateRequest(BaseModel):
    exam: str
    exam_date: str
    skill_gaps: list[dict]


class RecommendRequest(BaseModel):
    weak_skills: list[str]
    available_lessons: list[dict]


class FeedbackRequest(BaseModel):
    skill: str
    question: str
    student_answer: str
    correct_answer: str
    is_correct: bool


class PredictRequest(BaseModel):
    skill_history: list[dict]


@router.get("/ai/health")
async def ai_health():
    """Check if AI service is available."""
    available = await ai_service.is_available()
    return {"available": available, "model": ai_service.MODEL}


@router.post("/ai/generate-plan")
async def generate_plan(req: PlanGenerateRequest):
    """Generate a personalized study plan using AI."""
    if not await ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service unavailable")
    try:
        return await ai_service.generate_study_plan(req.exam, req.exam_date, req.skill_gaps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@router.post("/ai/recommend")
async def recommend(req: RecommendRequest):
    """Get AI-powered lesson recommendations."""
    if not await ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service unavailable")
    try:
        return await ai_service.recommend_lessons(req.weak_skills, req.available_lessons)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI recommendation failed: {str(e)}")


@router.post("/ai/feedback")
async def feedback(req: FeedbackRequest):
    """Get AI-generated targeted feedback."""
    if not await ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service unavailable")
    try:
        result = await ai_service.generate_feedback(
            req.skill, req.question, req.student_answer, req.correct_answer, req.is_correct
        )
        return {"feedback": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI feedback failed: {str(e)}")


@router.post("/ai/predict")
async def predict(req: PredictRequest):
    """Predict student performance."""
    if not await ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service unavailable")
    try:
        return await ai_service.predict_performance(req.skill_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI prediction failed: {str(e)}")
