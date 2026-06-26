from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


def _parse_json_response(text: str) -> dict:
    import json
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)


def _grade_essay_with_llm(prompt: str, essay: str) -> dict:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from seed_questions import chat_completion

    grading_prompt = f"""Grade this SAT-style essay on a 1-4 rubric for Reading, Analysis, Writing.
Prompt: {prompt}
Essay: {essay}

Respond ONLY in JSON:
{{
  "overall": int,
  "rubric": {{"reading": int, "analysis": int, "writing": int}},
  "comments": [str],
  "suggestions": [str]
}}"""
    raw = chat_completion(grading_prompt)
    return _parse_json_response(raw)


@router.post("/submit", response_model=schemas.WritingSubmissionResponse, status_code=201)
def submit_essay(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    submission_in: schemas.WritingSubmissionCreate,
) -> models.WritingSubmission:
    return crud.create_writing_submission(db, submission_in)


@router.get("/student/{student_id}", response_model=list[schemas.WritingSubmissionResponse])
def list_essays(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.WritingSubmission]:
    return crud.get_writing_submissions_by_student(db, student_id)


@router.post("/{submission_id}/grade", response_model=schemas.WritingSubmissionResponse)
def grade_essay(
    submission_id: str,
    db: Session = Depends(get_db),
    _teacher: models.User = Depends(get_current_user),
) -> models.WritingSubmission:
    sub = crud.get_writing_submission(db, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    try:
        feedback = _grade_essay_with_llm(sub.prompt, sub.essay_text)
    except Exception:
        feedback = {
            "overall": 0,
            "rubric": {"reading": 0, "analysis": 0, "writing": 0},
            "comments": ["Unable to generate AI feedback. Please try again."],
            "suggestions": [],
        }

    sub.ai_feedback = feedback
    sub.status = "graded"
    db.commit()
    db.refresh(sub)
    return sub


@router.get("/{submission_id}", response_model=schemas.WritingSubmissionResponse)
def get_essay(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.WritingSubmission:
    sub = crud.get_writing_submission(db, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return sub
