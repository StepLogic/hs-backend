import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app import crud


def sha1_key(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--storage", choices=["local", "b2"], default="local")
    parser.add_argument("--no-tts", action="store_true", default=False)
    args = parser.parse_args()

    base_dir = os.path.join(os.path.dirname(__file__), "..")
    curriculum_path = os.path.join(base_dir, "curriculum", "spanish.json")
    with open(curriculum_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    language = manifest["language"]
    voice = manifest["voice"]
    lang = manifest["lang"]
    slow_speed = manifest["slow_speed"]

    audio_dir = os.path.join(base_dir, "audio", language)
    os.makedirs(audio_dir, exist_ok=True)

    db = SessionLocal()
    try:
        for unit in manifest["units"]:
            unit_id = unit["id"]
            unit_title = unit["title"]
            for lesson in unit["lessons"]:
                lesson_title = lesson["title"]
                lesson_order = lesson["order"]
                db_lesson = crud.upsert_lesson(
                    db, language, unit_id, unit_title, lesson_title, lesson_order
                )
                # Remove old items to rebuild idempotently
                existing_items = crud.get_lesson_items(db, db_lesson.id)
                for item in existing_items:
                    db.delete(item)
                db.commit()

                for idx, item in enumerate(lesson["items"]):
                    text = item["text"]
                    item_type = item["type"]
                    audio_id = None
                    audio_slow_id = None

                    if not args.no_tts and item_type in ("listen", "repeat", "dictation"):
                        key = f"{language}/{sha1_key(text)}_1.0.wav"
                        path = os.path.join(audio_dir, f"{sha1_key(text)}_1.0.wav")
                        slow_key = f"{language}/{sha1_key(text)}_{slow_speed}.wav"
                        slow_path = os.path.join(audio_dir, f"{sha1_key(text)}_{slow_speed}.wav")

                        # Placeholder / generate
                        if not os.path.exists(path):
                            with open(path, "wb") as wf:
                                wf.write(b"")
                        if not os.path.exists(slow_path):
                            with open(slow_path, "wb") as wf:
                                wf.write(b"")

                        db_audio = crud.upsert_audio_asset(db, language, text, voice, 1.0, key)
                        db_audio_slow = crud.upsert_audio_asset(db, language, text, voice, slow_speed, slow_key)
                        audio_id = db_audio.id
                        audio_slow_id = db_audio_slow.id

                    crud.create_lesson_item(
                        db,
                        lesson_id=db_lesson.id,
                        order=idx,
                        type_=item_type,
                        text=text,
                        prompt=item.get("prompt"),
                        translation=item.get("translation"),
                        audio_id=audio_id,
                        audio_slow_id=audio_slow_id,
                        options=item.get("options"),
                        items=item.get("items"),
                        correct_answer=item.get("correct_answer"),
                        explanation=item.get("explanation"),
                        hint=item.get("hint"),
                    )

            # Process unit review poem
            review = unit["review"]
            poem_text = review["poem_text"]
            questions = review["questions"]
            poem_audio_id = None

            if not args.no_tts:
                key = f"{language}/{sha1_key(poem_text)}_1.0.wav"
                path = os.path.join(audio_dir, f"{sha1_key(poem_text)}_1.0.wav")
                if not os.path.exists(path):
                    with open(path, "wb") as wf:
                        wf.write(b"")
                db_audio = crud.upsert_audio_asset(db, language, poem_text, voice, 1.0, key)
                poem_audio_id = db_audio.id

            crud.upsert_unit_review(
                db, language, unit_id, unit_title, poem_text, questions,
                poem_audio_id=poem_audio_id,
            )

        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
