"""OLLAMA AI service for personalized learning features."""
import json
import os
from typing import Optional

import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "gemma3:latest")
TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "30"))


async def _prompt(system: str, user: str) -> str:
    """Send a prompt to OLLAMA and return the response."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        res = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODEL, "prompt": f"{system}\n\n{user}", "stream": False},
        )
        res.raise_for_status()
        return res.json()["response"].strip()


async def is_available() -> bool:
    """Check if OLLAMA is reachable."""
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            res = await client.get(f"{OLLAMA_URL}/api/tags")
            return res.is_success
    except Exception:
        return False


async def generate_study_plan(
    exam: str,
    exam_date: str,
    skill_gaps: list[dict],
) -> dict:
    """Generate a personalized study plan from skill gaps."""
    system = "You are an expert tutor creating personalized study plans. Output ONLY valid JSON, no markdown."
    gaps_text = "\n".join(
        f"- {g['skill']} ({g.get('area', 'General')}): mastery {g.get('current_mastery', 0)}%, priority {g.get('priority', 'medium')}"
        for g in skill_gaps
    )
    user = f"""Create a study plan for the {exam} exam. Target date: {exam_date}.
Skill gaps:
{gaps_text}

Return JSON:
{{"title": "string", "items": [{{"title": "string", "description": "string", "priority": "high|medium|low", "estimated_days": number}}]}}
Focus high-priority gaps first. Include 5-8 items."""

    raw = await _prompt(system, user)
    raw = raw.replace("```json\n", "").replace("```\n", "").replace("```", "").strip()
    return json.loads(raw)


async def recommend_lessons(
    weak_skills: list[str],
    available_lessons: list[dict],
) -> list[dict]:
    """Recommend lessons based on weak skills."""
    system = "You are a learning recommendation engine. Output ONLY valid JSON array."
    lessons_text = "\n".join(
        f"- {l['title']} (skills: {', '.join(l.get('skills', []))})"
        for l in available_lessons[:20]
    )
    user = f"""Student weak areas: {', '.join(weak_skills[:5])}.
Available lessons:
{lessons_text}

Return a JSON array of up to 5 recommended lesson titles with a brief reason:
[{{"title": "string", "reason": "string"}}]"""

    raw = await _prompt(system, user)
    raw = raw.replace("```json\n", "").replace("```\n", "").replace("```", "").strip()
    return json.loads(raw)


async def generate_feedback(
    skill: str,
    question: str,
    student_answer: str,
    correct_answer: str,
    is_correct: bool,
) -> str:
    """Generate targeted feedback for a student's answer."""
    system = "You are a supportive tutor. Give ONE short, encouraging feedback message (max 150 chars)."
    status = "correct" if is_correct else "incorrect"
    user = f"""Skill: {skill}
Question: {question}
Student answer: {student_answer}
Correct answer: {correct_answer}
Result: {status}

Give brief, specific feedback."""

    return await _prompt(system, user)


async def predict_performance(
    skill_history: list[dict],
) -> dict:
    """Predict student performance based on skill history."""
    system = "You are an educational data analyst. Output ONLY valid JSON."
    history_text = "\n".join(
        f"- {h['skill']}: {h['mastery_score']}% mastery, {h.get('attempts', 0)} attempts"
        for h in skill_history[:10]
    )
    user = f"""Skill history:
{history_text}

Predict: which skills will reach 80%+ mastery within 2 weeks, and which need most attention.
Return: {{"on_track": ["skill1"], "needs_attention": ["skill2"], "summary": "one sentence"}}"""

    raw = await _prompt(system, user)
    raw = raw.replace("```json\n", "").replace("```\n", "").replace("```", "").strip()
    return json.loads(raw)
