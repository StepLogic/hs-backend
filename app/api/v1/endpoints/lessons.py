from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db
from app.config import settings

router = APIRouter()


def _build_audio_url(audio_asset: models.AudioAsset | None) -> str | None:
    if not audio_asset:
        return None
    return f"{settings.AUDIO_BASE_URL}/{audio_asset.key}"


@router.get("/", response_model=list[schemas.LessonSummaryResponse])
def read_lessons(
    db: Session = Depends(get_db),
    language: str = Query("spanish"),
) -> list[models.Lesson]:
    return crud.get_lessons(db, language=language)


@router.get("/{lesson_id}", response_model=schemas.LessonResponse)
def read_lesson(lesson_id: str, db: Session = Depends(get_db)) -> dict:
    lesson = crud.get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    items = []
    for item in lesson.items:
        items.append({
            "id": item.id,
            "order": item.order,
            "type": item.type.value,
            "prompt": item.prompt,
            "text": item.text,
            "translation": item.translation,
            "audio_url": _build_audio_url(item.audio),
            "audio_slow_url": _build_audio_url(item.audio_slow),
            "options": item.options,
            "items": item.items,
            "correct_answer": item.correct_answer,
            "explanation": item.explanation,
            "hint": item.hint,
        })
    return {
        "id": lesson.id,
        "language": lesson.language.value,
        "unit": lesson.unit,
        "unit_title": lesson.unit_title,
        "title": lesson.title,
        "order": lesson.order,
        "items": items,
    }
