from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db, get_current_user

router = APIRouter()


def _build_system_prompt(subject: str | None) -> str:
    base = "You are a patient, encouraging K–12 tutor. Explain concepts clearly, use examples, and ask guiding questions rather than giving answers outright."
    if subject:
        base += f" You are currently tutoring {subject.value if hasattr(subject, 'value') else subject}."
    return base


def _call_llm(messages: list[dict]) -> str:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from seed_questions import chat_completion

    prompt_parts = []
    for msg in messages:
        prompt_parts.append(f"{msg['role'].upper()}: {msg['content']}")
    prompt_parts.append("ASSISTANT:")
    full_prompt = "\n\n".join(prompt_parts)
    return chat_completion(full_prompt)


@router.post("/chat", response_model=dict)
def tutor_chat(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    student_id: str,
    session_id: str | None = None,
    message: str,
    subject: str | None = None,
) -> dict:
    # Fetch or create session
    chat_session = None
    if session_id:
        chat_session = crud.get_chat_session(db, session_id)
    if not chat_session:
        chat_session = crud.create_chat_session(
            db,
            schemas.ChatSessionCreate(
                student_id=student_id,
                subject=models.Subject(subject) if subject else None,
                title=message[:50] if message else None,
            ),
        )
        session_id = str(chat_session.id)

    # Persist user message
    crud.create_chat_message(db, session_id, "user", message)

    # Build context (last 20 messages)
    history = crud.get_chat_messages(db, session_id)
    context = [{"role": "system", "content": _build_system_prompt(chat_session.subject)}]
    for msg in history[-20:]:
        context.append({"role": msg.role, "content": msg.content})

    # Get AI response
    try:
        ai_content = _call_llm(context)
    except Exception:
        ai_content = "I'm having trouble connecting right now. Please try again in a moment."

    # Persist assistant response
    crud.create_chat_message(db, session_id, "assistant", ai_content)

    return {
        "session_id": session_id,
        "response": ai_content,
    }


@router.get("/history/{session_id}", response_model=schemas.ChatHistoryResponse)
def chat_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict:
    session = crud.get_chat_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = crud.get_chat_messages(db, session_id)
    return {
        "session_id": session_id,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
    }
