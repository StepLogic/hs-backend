#!/usr/bin/env python3
"""Seed questions into the hs-backend database using cloud LLM APIs."""

import json
import os
import re
import sys
import urllib.request

BACKEND_URL = os.getenv("BACKEND_URL", "https://hs-backend-75yy.onrender.com/api/v1")

# --- Cloud LLM config ---
# Set ONE of: OLLAMA_CLOUD_API_KEY, GROQ_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY
OLLAMA_CLOUD_API_KEY = os.getenv("OLLAMA_CLOUD_API_KEY", "e3c5eaf7f2714e9b8cabb9449ed93823.ZCmNdvpuLKvNhKcky4qg9Gj_")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Optional: override the default model for each provider
OLLAMA_CLOUD_MODEL = os.getenv("OLLAMA_CLOUD_MODEL", "gemma4:31b-cloud")
GROQ_MODEL = os.getenv("GROQ_MODEL", "gemma2-9b-it")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemma-3-27b-it")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-3-27b-it:free")

if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)
    OLLAMA_CLOUD_API_KEY = os.getenv("OLLAMA_CLOUD_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OLLAMA_CLOUD_MODEL = os.getenv("OLLAMA_CLOUD_MODEL", OLLAMA_CLOUD_MODEL)
    GROQ_MODEL = os.getenv("GROQ_MODEL", GROQ_MODEL)
    GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", GOOGLE_MODEL)
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", OPENAI_MODEL)
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", OPENROUTER_MODEL)

LOCAL_MODE = "DATABASE_URL" in os.environ and "SECRET_KEY" in os.environ


def chat_completion(prompt: str) -> str:
    """Call a cloud chat completion API."""
    if OLLAMA_CLOUD_API_KEY:
        return _ollama_cloud_chat(prompt)
    if GROQ_API_KEY:
        return _groq_chat(prompt)
    if GOOGLE_API_KEY:
        return _google_chat(prompt)
    if OPENAI_API_KEY:
        return _openai_chat(prompt)
    if OPENROUTER_API_KEY:
        return _openrouter_chat(prompt)
    raise RuntimeError(
        "No cloud API key found. Set one of:\n"
        "  OLLAMA_CLOUD_API_KEY   (gemma4:31b-cloud, no local disk needed)\n"
        "  GROQ_API_KEY           (fast, free tier)\n"
        "  GOOGLE_API_KEY         (Google AI Studio, free tier)\n"
        "  OPENAI_API_KEY\n"
        "  OPENROUTER_API_KEY"
    )


def _ollama_cloud_chat(prompt: str) -> str:
	"""Ollama Cloud API — hosts models remotely, no local download."""
	url = "https://ollama.com/api/chat"
	headers = {
		"Authorization": f"Bearer {OLLAMA_CLOUD_API_KEY}",
		"Content-Type": "application/json",
	}
	payload = {
		"model": OLLAMA_CLOUD_MODEL,
		"messages": [
			{"role": "system", "content": "You are an expert K-12 curriculum designer. Return ONLY valid JSON. No markdown. No explanations."},
			{"role": "user", "content": prompt},
		],
		"stream": False,
		"format": "json",
	}
	data = json.dumps(payload).encode()
	req = urllib.request.Request(url, data=data, headers=headers)
	with urllib.request.urlopen(req, timeout=120) as resp:
		body = json.loads(resp.read().decode())
		return body["message"]["content"]


def _groq_chat(prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert K-12 curriculum designer. Return ONLY valid JSON. No markdown. No explanations."},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode())
        return body["choices"][0]["message"]["content"]


def _google_chat(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GOOGLE_MODEL}:generateContent?key={GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": "You are an expert K-12 curriculum designer. Return ONLY valid JSON. No markdown. No explanations.\n\n" + prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
        },
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode())
        return body["candidates"][0]["content"]["parts"][0]["text"]


def _openai_chat(prompt: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert K-12 curriculum designer. Return ONLY valid JSON. No markdown. No explanations."},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode())
        return body["choices"][0]["message"]["content"]


def _openrouter_chat(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://homeschool.local",
        "X-Title": "HS Platform Seeder",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert K-12 curriculum designer. Return ONLY valid JSON. No markdown. No explanations."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode())
        return body["choices"][0]["message"]["content"]


def parse_json_response(text: str) -> list | dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def generate_questions(subject: str, grade_level: int, skill: str, count: int = 5, difficulty: str = "medium", review_status: str = "draft") -> list[dict]:
    prompt = f"""Generate {count} homeschool assessment questions for the subject \"{subject.upper()}\" at grade level {grade_level}, skill \"{skill}\", difficulty \"{difficulty}\".

Return ONLY a JSON object with exactly this structure:
{{\"questions\":[{{\"subject\":\"{subject}\",\"grade_level\":{grade_level},\"type\":\"multiple-choice\",\"prompt\":\"What is 2 + 3?\",\"context\":null,\"options\":[\"4\",\"5\",\"6\",\"7\"],\"correct_answer\":\"5\",\"skill\":\"{skill}\",\"explanation\":\"When you add 2 and 3 you get 5.\",\"hint\":\"Count on your fingers.\"}}]}}

Rules:
- subject must be exactly \"{subject}\"
- grade_level must be integer {grade_level}
- type must be exactly \"multiple-choice\" or \"fill-in\"
- options must be a flat array of exactly 4 strings for multiple-choice, or null for fill-in
- correct_answer must exactly match one value from options
- skill must be exactly \"{skill}\"
- difficulty must be exactly \"{difficulty}\"
- hint may be null or a short string
- All strings must use double quotes
- No trailing commas
"""
    response = chat_completion(prompt)
    parsed = parse_json_response(response)
    questions = parsed if isinstance(parsed, list) else parsed.get("questions", [])

    normalized = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        required = ("subject", "grade_level", "type", "prompt", "correct_answer", "skill", "explanation")
        if not all(k in q for k in required):
            continue
        try:
            q["grade_level"] = int(q["grade_level"])
        except (ValueError, TypeError):
            q["grade_level"] = grade_level
        for k in ("context", "options", "pairs", "items", "hint"):
            if k not in q:
                q[k] = None
        if q.get("options") and isinstance(q["options"], list):
            flat = []
            for opt in q["options"]:
                if isinstance(opt, str):
                    flat.append(opt)
                elif isinstance(opt, dict) and "text" in opt:
                    flat.append(str(opt["text"]))
            q["options"] = flat if flat else None
        if not isinstance(q.get("correct_answer"), str):
            q["correct_answer"] = str(q["correct_answer"])
        q["subject"] = str(q.get("subject", "")).strip().lower()
        # Accept both old and new subject values
        valid_subjects = (
            "math", "reading", "comprehension", "english_language_arts",
            "science", "social_studies", "world_languages", "test_prep", "college_readiness",
        )
        if q["subject"] not in valid_subjects:
            continue
        q["type"] = str(q.get("type", "")).strip().lower().replace("_", "-")
        if q["type"] not in ("multiple-choice", "fill-in", "ordering", "matching"):
            q["type"] = "multiple-choice"
        skill_val = str(q.get("skill") or "").strip().lower()
        if not skill_val:
            skill_val = q["subject"]
        q["skill"] = skill_val
        if "type" in q:
            q["question_type"] = q.pop("type")
        q["difficulty"] = q.get("difficulty", difficulty)
        q["review_status"] = review_status
        normalized.append(q)
    return normalized


def generate_lesson(subject: str, topic: str, grade_level: int) -> dict:
    prompt = f"""Create a homeschool lesson for the subject \"{subject.upper()}\" on the topic \"{topic}\" for grade level {grade_level}.

Return ONLY a JSON object with exactly this structure:
{{\"title\":\"Lesson Title\",\"content\":\"# Lesson Title\\n\\n## Objectives\\n- Objective 1\\n\\n## Explanation\\nBody text here.\\n\\n## Worked Examples\\nExample 1...\\n\\n## Practice Pointers\\nTry these...\",\"skills\":[\"skill1\",\"skill2\"]}}

Rules:
- title must be a short, catchy title
- content must be valid Markdown with sections: Objectives, Explanation, Worked Examples, Practice Pointers
- skills must be an array of lowercase strings
- All strings must use double quotes
- No trailing commas
"""
    response = chat_completion(prompt)
    parsed = parse_json_response(response)
    if not isinstance(parsed, dict):
        parsed = {}
    return {
        "title": parsed.get("title", f"{topic.title()}"),
        "content": parsed.get("content", f"# {topic.title()}\\n\\nLesson content coming soon."),
        "skills": parsed.get("skills", [topic.lower().replace(" ", "_")]),
    }


def seed_via_api(questions: list[dict]) -> int:
    url = f"{BACKEND_URL}/questions"
    success = 0
    for q in questions:
        payload = dict(q)
        if "question_type" in payload:
            payload["type"] = payload.pop("question_type")
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status in (200, 201):
                    success += 1
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code}: {e.read().decode()[:200]}")
        except Exception as e:
            print(f"  Error: {e}")
    return success


def seed_via_db(questions: list[dict]) -> int:
    from app.database import SessionLocal
    from app import models

    db = SessionLocal()
    success = 0
    try:
        for q in questions:
            try:
                db_question = models.Question(**q)
                db.add(db_question)
                db.commit()
                success += 1
            except Exception as e:
                db.rollback()
                print(f"  DB error: {e}")
    finally:
        db.close()
    return success


def main():
    provider = "unknown"
    model = "unknown"
    if OLLAMA_CLOUD_API_KEY:
        provider = "Ollama Cloud"
        model = OLLAMA_CLOUD_MODEL
    elif GROQ_API_KEY:
        provider = "Groq"
        model = GROQ_MODEL
    elif GOOGLE_API_KEY:
        provider = "Google AI Studio"
        model = GOOGLE_MODEL
    elif OPENAI_API_KEY:
        provider = "OpenAI"
        model = OPENAI_MODEL
    elif OPENROUTER_API_KEY:
        provider = "OpenRouter"
        model = OPENROUTER_MODEL

    subjects = [
        ("math", list(range(0, 13))),
        ("reading", list(range(0, 13))),
        ("comprehension", list(range(1, 13))),
    ]
    total_questions = []

    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"Mode: {'local DB' if LOCAL_MODE else 'API (' + BACKEND_URL + ')'}")
    print()

    for subject, grades in subjects:
        for grade in grades:
            print(f"Generating {subject} questions for grade {grade} ...", end=" ", flush=True)
            try:
                questions = generate_questions(subject, grade, count=3)
                print(f"got {len(questions)}")
                total_questions.extend(questions)
            except Exception as e:
                print(f"FAILED: {e}")
                continue

    if not total_questions:
        print("No questions generated. Exiting.")
        sys.exit(1)

    print(f"\nTotal generated: {len(total_questions)}")
    print(f"Seeding into {'local DB' if LOCAL_MODE else 'API'} ...")

    if LOCAL_MODE:
        success = seed_via_db(total_questions)
    else:
        success = seed_via_api(total_questions)

    print(f"Inserted {success}/{len(total_questions)} questions successfully.")


if __name__ == "__main__":
    main()
