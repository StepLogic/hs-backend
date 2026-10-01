#!/usr/bin/env python3
"""Restore the figures the SAT import dropped: images, their descriptions, and data tables.

The scrape (data/all_sat_questions.json) carries `image` (a filename in the source's S3
bucket), `visual_element` (a text description of that image) and `table`. The import
kept none of them, so graph and table questions came through unanswerable. This matches
each stored question back to the scrape, copies its image to our B2 bucket, and writes
image_url / image_alt / figure_table.

    python scripts/backfill_question_figures.py data/all_sat_questions.json          # dry run
    python scripts/backfill_question_figures.py data/all_sat_questions.json --apply

Images are cached in data/sat_images/, so a re-run downloads nothing it already has.
"""
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import models  # noqa: E402
from app.b2 import PUBLIC_BASE, get_bucket  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from scripts.seed_sat_questions import map_context  # noqa: E402

SOURCE = "https://test-ninjas-sat-questions.s3.us-west-2.amazonaws.com/"
CACHE = Path(__file__).parent.parent / "data" / "sat_images"
KEY_PREFIX = "questions/sat/"


def _key(source_test_id, prompt, context, answer) -> tuple:
    return tuple(str(v or "").strip() for v in (source_test_id, prompt, context, answer))


def figures(flat: list) -> dict:
    """Scrape key -> its figure fields, for the questions that have any."""
    out = {}
    for q in flat:
        if not (q.get("image") or q.get("table")):
            continue
        k = _key(q.get("_source_test_id") or q.get("test_id") or "unknown",
                 q.get("question"), map_context(q.get("passage")), q.get("correct_answer"))
        out[k] = {"image": q.get("image") or None,
                  "alt": q.get("visual_element") or None,
                  "table": q.get("table") or None}
    return out


def fetch(name: str) -> bytes:
    path = CACHE / name
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(SOURCE + name, timeout=30) as r:
            path.write_bytes(r.read())
    return path.read_bytes()


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--apply"]
    apply = "--apply" in sys.argv
    if len(args) != 1:
        sys.exit(__doc__)
    wanted = figures(json.load(open(args[0])))
    print(f"{len(wanted)} questions in the scrape have a figure")

    db = SessionLocal()
    try:
        # Only pre-existing columns, so the dry run works before the migration has run.
        Q = models.Question
        matched = defaultdict(list)
        for qid, *fields in db.query(Q.id, Q.source_test_id, Q.prompt, Q.context, Q.correct_answer
                                     ).filter(Q.source_test_id.isnot(None)):
            k = _key(*fields)
            if k in wanted:
                matched[k].append(qid)
        rows = sum(len(v) for v in matched.values())
        print(f"{len(matched)} of them found in the table ({rows} rows, duplicates included)")

        images = sorted({wanted[k]["image"] for k in matched if wanted[k]["image"]})
        print(f"{len(images)} images to copy to B2")
        if not apply:
            print("dry run; pass --apply to download, upload and write")
            return

        bucket = get_bucket()
        urls, failed = {}, []
        for i, name in enumerate(images, 1):
            try:
                bucket.upload_bytes(fetch(name), KEY_PREFIX + name, content_type="image/png")
                urls[name] = f"{PUBLIC_BASE}/{KEY_PREFIX}{name}"
            except Exception as e:  # one bad file should not lose the rest
                failed.append((name, str(e)))
            if i % 50 == 0:
                print(f"  {i}/{len(images)} images")

        for k, group in matched.items():
            f = wanted[k]
            for row in db.query(Q).filter(Q.id.in_(group)):
                if f["image"] in urls:
                    row.image_url, row.image_alt = urls[f["image"]], f["alt"]
                if f["table"]:
                    row.figure_table = f["table"]
        db.commit()
        print(f"written; {len(urls)} images uploaded, {len(failed)} failed")
        for name, err in failed:
            print(f"  FAILED {name}: {err}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
