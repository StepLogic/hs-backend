import os

import resend

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def send_parent_digest(parent_email: str, student_data: list[dict]) -> dict:
    """Send a weekly email digest to a parent summarizing student activity."""
    if not RESEND_API_KEY:
        return {"sent": False, "reason": "RESEND_API_KEY not configured"}

    lines = [f"<h2>Weekly Activity Digest</h2>"]
    for s in student_data:
        lines.append(f"<h3>{s.get('name', 'Student')}</h3>")
        lines.append(f"<p>Time spent this week: {s.get('time_spent_minutes', 0)} min</p>")
        lines.append(f"<p>Tests completed: {s.get('tests_completed', 0)}</p>")
        lines.append(f"<p>Average score: {s.get('average_score', 'N/A')}</p>")

    html = "<div>" + "\n".join(lines) + "</div>"

    params: resend.Email = {
        "from": FROM_EMAIL,
        "to": parent_email,
        "subject": "Your Weekly Student Digest",
        "html": html,
    }

    try:
        response = resend.Emails.send(params)
        return {"sent": True, "id": response.get("id")}
    except Exception as e:
        return {"sent": False, "reason": str(e)}


def notify_student(student_id: str, event: str, data: dict) -> dict:
    """Record a notification event for a student (placeholder for push/email)."""
    # ponytail: placeholder — wire to actual push/email provider when needed
    return {"student_id": student_id, "event": event, "recorded": True, "data": data}
