import argparse
import hashlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app import crud, models


def sha1_key(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def generate_audio(text: str, voice: str, speed: float, lang: str, model_dir: str) -> bytes:
    from kokoro_onnx import Kokoro
    import soundfile as sf

    kokoro = Kokoro(
        os.path.join(model_dir, "kokoro-v1.0.onnx"),
        os.path.join(model_dir, "voices-v1.0.bin"),
    )
    samples, sr = kokoro.create(text, voice=voice, speed=speed, lang=lang)
    buf = io.BytesIO()
    sf.write(buf, samples, sr, format="WAV")
    return buf.getvalue()


def upload_b2(key: str, data: bytes, bucket_name: str) -> None:
    from b2sdk.v2 import B2Api, InMemoryAccountInfo

    info = InMemoryAccountInfo()
    b2 = B2Api(info)
    b2.authorize_account(
        "production",
        os.environ["B2_KEY_ID"],
        os.environ["B2_APP_KEY"],
    )
    bucket = b2.get_bucket_by_name(bucket_name)
    try:
        bucket.get_file_info_by_name(key)
        print(f"  [skip] {key} already exists in B2")
    except Exception:
        bucket.upload_bytes(data, key)
        print(f"  [upload] {key}")


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

    model_dir = os.environ.get("KOKORO_MODEL_DIR", os.path.join(base_dir, "models"))
    bucket_name = os.environ.get("B2_BUCKET")

    if args.storage == "b2" and not bucket_name:
        print("ERROR: B2_BUCKET env var required for --storage b2")
        sys.exit(1)

    # Verify voice exists (fallback to first e* voice)
    if not args.no_tts:
        from kokoro_onnx import Kokoro
        test_kokoro = Kokoro(
            os.path.join(model_dir, "kokoro-v1.0.onnx"),
            os.path.join(model_dir, "voices-v1.0.bin"),
        )
        voices = test_kokoro.get_voices()
        if voice not in voices:
            fallback = next((v for v in voices if v.startswith("e")), None)
            if fallback:
                print(f"Voice {voice} not found; falling back to {fallback}")
                voice = fallback
            else:
                print(f"WARNING: Voice {voice} not found and no fallback available")

    db = SessionLocal()
    try:
        total_generated = 0
        total_skipped = 0

        for unit in manifest["units"]:
            unit_id = unit["id"]
            unit_title = unit["title"]
            for lesson in unit["lessons"]:
                lesson_title = lesson["title"]
                lesson_order = lesson["order"]

                db_lesson = crud.upsert_lesson(
                    db,
                    language=models.Language.SPANISH,
                    unit=unit_id,
                    unit_title=unit_title,
                    title=lesson_title,
                    order=lesson_order,
                )

                for idx, item in enumerate(lesson["items"]):
                    text = item["text"]
                    item_type = item["type"]
                    audio_id = None
                    audio_slow_id = None

                    if not args.no_tts and item_type in ("listen", "repeat", "dictation"):
                        for speed in (1.0, slow_speed if item_type == "repeat" else None):
                            if speed is None:
                                continue
                            key = f"{language}/{sha1_key(text)}_{speed}.wav"
                            path = os.path.join(audio_dir, f"{sha1_key(text)}_{speed}.wav")

                            if args.storage == "local":
                                if not os.path.exists(path):
                                    wav = generate_audio(text, voice, speed, lang, model_dir)
                                    with open(path, "wb") as wf:
                                        wf.write(wav)
                                    print(f"  [gen] {key}")
                                    total_generated += 1
                                else:
                                    print(f"  [skip] {key}")
                                    total_skipped += 1
                            elif args.storage == "b2":
                                wav = generate_audio(text, voice, speed, lang, model_dir)
                                upload_b2(key, wav, bucket_name)
                                total_generated += 1

                            db_audio = crud.upsert_audio_asset(
                                db, models.Language.SPANISH, text, voice, speed, key
                            )
                            if speed == 1.0:
                                audio_id = db_audio.id
                            else:
                                audio_slow_id = db_audio.id

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

                if args.storage == "local":
                    if not os.path.exists(path):
                        wav = generate_audio(poem_text, voice, 1.0, lang, model_dir)
                        with open(path, "wb") as wf:
                            wf.write(wav)
                        print(f"  [gen] {key}")
                        total_generated += 1
                    else:
                        print(f"  [skip] {key}")
                        total_skipped += 1
                elif args.storage == "b2":
                    wav = generate_audio(poem_text, voice, 1.0, lang, model_dir)
                    upload_b2(key, wav, bucket_name)
                    total_generated += 1

                db_audio = crud.upsert_audio_asset(
                    db, models.Language.SPANISH, poem_text, voice, 1.0, key
                )
                poem_audio_id = db_audio.id

            crud.upsert_unit_review(
                db,
                models.Language.SPANISH,
                unit_id,
                unit_title,
                poem_text,
                questions,
                poem_audio_id=poem_audio_id,
            )

        print(f"Done. Generated: {total_generated}, Skipped: {total_skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
