"""Patch an existing lesson's video content block without re-importing the course.

Usage:
    python3 patch_lesson_video.py

This finds the "Solving Linear Equations" lesson in the SAT Math Prep course
and updates its first content block to use the new YouTube embed URL.
"""
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BACKEND_URL = os.getenv("BACKEND_URL", "https://hs-backend-75yy.onrender.com/api/v1")
NEW_VIDEO_SRC = "https://www.youtube.com/embed/aTsc4WIT2cs?si=WIH5QxvSjkwW8z0k"


def api_call(method: str, path: str, data: dict | None = None):
    url = f"{BACKEND_URL}{path}"
    headers = {"Accept": "application/json"}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except HTTPError as e:
        err = e.read().decode()
        print(f"HTTP {e.code}: {err}")
        return None, e.code


def main():
    # Find SAT Math Prep course
    courses, status = api_call("GET", "/courses")
    if not courses:
        print("Failed to fetch courses")
        sys.exit(1)

    sat_course = next(
        (c for c in courses if "SAT" in c.get("title", "")), None
    )
    if not sat_course:
        print("SAT course not found")
        sys.exit(1)
    print(f"Found course: {sat_course['id']} - {sat_course['title']}")

    # Find the lesson
    units, status = api_call("GET", f"/units/course/{sat_course['id']}")
    if not units:
        print("Failed to fetch units")
        sys.exit(1)

    target_lesson = None
    for unit in units:
        lessons, status = api_call("GET", f"/lessons/unit/{unit['id']}")
        if lessons:
            for lesson in lessons:
                if lesson.get("title") == "Solving Linear Equations":
                    target_lesson = lesson
                    print(f"Found lesson: {lesson['id']} in unit {unit['id']}")
                    break
        if target_lesson:
            break

    if not target_lesson:
        print("Lesson 'Solving Linear Equations' not found")
        sys.exit(1)

    # Update content_blocks — replace video block or insert at top
    content_blocks = target_lesson.get("content_blocks") or []
    new_blocks = [b for b in content_blocks if b.get("type") != "video"]
    new_blocks.insert(0, {
        "type": "video",
        "src": NEW_VIDEO_SRC,
        "caption": "Solving Linear Equations - Video Lesson"
    })

    result, status = api_call(
        "PUT", f"/lessons/{target_lesson['id']}", {"content_blocks": new_blocks}
    )
    if result:
        print(f"Updated lesson {target_lesson['id']} (HTTP {status})")
        for b in result.get("content_blocks", []):
            snippet = str(b.get("src", ""))[:70]
            print(f"  - {b.get('type')}: {snippet}...")
    else:
        print("Update failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
