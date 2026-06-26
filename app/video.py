import os
import uuid

import requests

DAILY_API_KEY = os.getenv("DAILY_API_KEY")


def create_room(name: str | None = None, expiry_min: int = 120) -> dict:
    if not DAILY_API_KEY:
        raise RuntimeError("DAILY_API_KEY not configured")
    room_name = name or str(uuid.uuid4())
    r = requests.post(
        "https://api.daily.co/v1/rooms",
        headers={"Authorization": f"Bearer {DAILY_API_KEY}"},
        json={
            "name": room_name,
            "privacy": "public",
            "properties": {
                "max_call_duration_secs": expiry_min * 60,
                "enable_screenshare": True,
            },
        },
    )
    r.raise_for_status()
    return r.json()
