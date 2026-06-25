from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db
from app.config import settings

router = APIRouter()


@router.get("/{unit}", response_model=schemas.UnitReviewResponse)
def read_review(unit: str, db: Session = Depends(get_db), language: str = Query("spanish")) -> dict:
    review = crud.get_unit_review(db, language=language, unit=unit)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    poem_audio_url = None
    if review.poem_audio_id:
        audio = crud.get_audio_asset(db, review.poem_audio_id)
        if audio:
            poem_audio_url = f"{settings.AUDIO_BASE_URL}/{audio.key}"
    return {
        "id": review.id,
        "language": review.language.value,
        "unit": review.unit,
        "unit_title": review.unit_title,
        "poem_text": review.poem_text,
        "poem_audio_url": poem_audio_url,
        "questions": review.questions,
    }
