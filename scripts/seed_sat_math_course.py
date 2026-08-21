#!/usr/bin/env python3
"""Build the SAT Math course from scraped YouTube videos + scraped SAT questions.

Shape (decided with the product owner):
    Course  "SAT Math"
      Unit    = one SAT math *skill*      (Nonlinear Equations, Circles, ...)
        Lesson  = one *video*             (embedded, plus a slice of that skill's questions)

Videos are matched to skills by keyword on their title. The map below is
deliberately explicit rather than clever: a wrong pairing puts a student in
front of the wrong explanation, so it needs to be readable and auditable by
someone who is not the person who wrote it.

    python scripts/seed_sat_math_course.py            # seed
    python scripts/seed_sat_math_course.py --reset    # rebuild from scratch
    python scripts/seed_sat_math_course.py --dry-run  # report, touch nothing
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import openpyxl
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import models

COURSE_SLUG = "sat-math"
MATH_DOMAINS = (
    "Algebra",
    "Advanced Math",
    "Problem-Solving and Data Analysis",
    "Geometry and Trigonometry",
)

# Unit order: SAT domain order, then skill. Every skill in the question bank gets
# a unit, including the three with no video — their questions still need a home.
SKILL_ORDER = [
    ("Algebra", "Linear Equations in One Variable"),
    ("Algebra", "Linear Equations in Two Variables"),
    ("Algebra", "Linear Functions"),
    ("Algebra", "System of Two Linear Equations"),
    ("Algebra", "Linear Inequalities"),
    ("Advanced Math", "Equivalent Expressions"),
    ("Advanced Math", "Nonlinear Equations"),
    ("Advanced Math", "Nonlinear Functions"),
    ("Problem-Solving and Data Analysis", "Ratios Rates Proportions"),
    ("Problem-Solving and Data Analysis", "Percentages"),
    ("Problem-Solving and Data Analysis", "One Variable Data"),
    ("Problem-Solving and Data Analysis", "Two Variable Data"),
    ("Problem-Solving and Data Analysis", "Probability"),
    ("Problem-Solving and Data Analysis", "Inference from Sample Statistics"),
    ("Problem-Solving and Data Analysis", "Evaluating Statistical Claims"),
    ("Geometry and Trigonometry", "Area and Volume"),
    ("Geometry and Trigonometry", "Lines Angles Triangles"),
    ("Geometry and Trigonometry", "Right Triangles and Trigonometry"),
    ("Geometry and Trigonometry", "Circles"),
]

# Order matters: the first skill whose keyword appears in the title wins, so more
# specific phrases must come before the generic ones they contain. "completing the
# square" has to beat "square"; "linear function" has to beat "function".
SKILL_KEYWORDS = [
    ("Circles", ["hidden radius", "circle", "radius", "circumference"]),
    ("Right Triangles and Trigonometry", ["pythagor", "right triangle", "sina vs cos", "trigonometry", "midpoint theorem"]),
    ("Lines Angles Triangles", ["transversal", "parallel lines", "area of triangles", "triangle"]),
    ("Area and Volume", ["perimeter", "area", "volume", "sphere", "cube root"]),
    ("Nonlinear Equations", ["quadratic", "completing the square", "discriminant", "roots of quadratic",
                             "sum and product of roots", "product of the roots", "aquad", "foil",
                             "roots, factors",
                             "absolute value", "identical equation"]),
    ("Nonlinear Functions", ["exponential function", "composition of function", "evaluating function",
                             "polynomial", "factor and remainder", "f of x", "axis of symmetry",
                             "intercept and function notation"]),
    ("System of Two Linear Equations", ["system of equation", "system of  equation", "sytem of equation"]),
    ("Linear Inequalities", ["inequalit"]),
    ("Linear Functions", ["linear function", "interpreting linear"]),
    ("Linear Equations in Two Variables", ["slope", "intercept", "distance between two points",
                                          "distance formula", "midpoint"]),
    ("Linear Equations in One Variable", ["one variable equation", "one-variable equation", "one viariable equation",
                                         "one-step", "two-step", "multi-step equation", "multi-step equations",
                                         "equation with fraction", "equations with fraction",
                                         "fractional coefficient", "variables on both sides",
                                         "isolation of quantities", "rewriting formulas", "cross multiplication",
                                         "fractions in linear equations",
                                         "cross-multiplication", "equations with parantheses"]),
    ("Percentages", ["percent", "discount", "commision", "commission", "interest", "income tax"]),
    ("Ratios Rates Proportions", ["ratio", "proportion"]),
    ("One Variable Data", ["mean, median", "mean median", "average", "frequency", "missing data"]),
    ("Two Variable Data", ["chart", "graph"]),
    ("Probability", ["probabilit"]),
    ("Equivalent Expressions", ["algebraic fraction", "complex fraction", "rational expression", "rational equation",
                                "radical", "rational exponent", "exponent", "like terms", "distributive",
                                "conjugate", "gcf", "lcm", "writing expression", "evaluating polynomial",
                                "terms involving fractions",
                                "evaluating multi-variable", "letters in algebra", "simplifying",
                                "simple algebraic", "factoring", "identical and system"]),
]

# Channel trailers, screen recordings and untitled uploads — not teaching content.
JUNK_TITLE = re.compile(
    r"^(ad$|ad \d|ad for|ratio ad|untitled|entire screen|sample respons|math with a student)",
    re.I,
)

# Videos that teach something real but sit below the SAT — arithmetic, long division,
# divisibility. Kept out of the SAT units rather than discarded silently.
FOUNDATION_KEYWORDS = [
    "integers", "divisibility", "division with", "three digit", "multiplication of one digit",
    "missing digits", "order of operations", "rounding", "prime factorization", "speed math",
    "mixed fractions", "word problems 1 primary", "introduction to variables elementary",
    "middle school", "beginning algebra", "problem solving set 1 fractions",
    "fractions word problems", "division and missing digits", "the four operations",
    "the value of each mark", "multi-step word problems", "linked thinking",
]


def classify(title: str) -> str | None:
    """Return the SAT skill this video teaches, 'FOUNDATIONS', or None."""
    if JUNK_TITLE.match(title.strip()):
        return None
    low = title.lower()
    for skill, keywords in SKILL_KEYWORDS:
        if any(k in low for k in keywords):
            return skill
    if any(k in low for k in FOUNDATION_KEYWORDS):
        return "FOUNDATIONS"
    return "FOUNDATIONS"


def duration_minutes(raw) -> int:
    """openpyxl reads '12:05' as 12h05m. It is really 12 minutes 5 seconds."""
    if isinstance(raw, timedelta):
        total = int(raw.total_seconds())
        return max(1, total // 3600 + (1 if (total % 3600) // 60 >= 30 else 0))
    if raw is None:
        return 10
    parts = str(raw).split(":")
    try:
        minutes, seconds = int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return 10
    return max(1, minutes + (1 if seconds >= 30 else 0))


_TRAILING_NUM = re.compile(r"(\d+)\s*$")
_INTRO = re.compile(r"^(introduction|intro|beginning|quick review|review)\b", re.I)


def lesson_sort_key(title: str) -> tuple:
    """Introductions first, then series grouped together and numbered in order.

    Sorting on the trailing number alone scatters a series, because the first part
    is usually unnumbered ("The Hidden Radius", "... 2", "... 3") and would sort
    last. Group on the title with its number stripped, then order within the group.
    """
    t = title.strip()
    m = _TRAILING_NUM.search(t)
    base = _TRAILING_NUM.sub("", t).strip().lower()
    return (0 if _INTRO.match(t) else 1, base, int(m.group(1)) if m else 0)


def slugify(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")[:80]


def map_difficulty(src) -> str:
    d = str(src or "").lower()
    return d if d in ("easy", "medium", "hard") else "medium"


def build_explanation(q: dict) -> str:
    parts = [str(q["explanation"])] if q.get("explanation") else []
    de = q.get("distractor_explanation")
    if de:
        parts.append("Distractor explanations:\n" + ("\n".join(map(str, de)) if isinstance(de, list) else str(de)))
    return "\n\n".join(parts) or "No explanation provided."


def map_context(passage) -> str | None:
    if not passage:
        return None
    if isinstance(passage, dict):
        return "\n\n".join(str(passage[k]) for k in sorted(passage))
    return str(passage)


DIFF_RANK = {"easy": 0, "medium": 1, "hard": 2}


def load_videos(path: Path) -> list[dict]:
    ws = openpyxl.load_workbook(path).active
    out = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        title, url = row[0], row[1]
        if not title or not url:
            continue
        skill = classify(str(title))
        if skill is None:
            continue
        out.append({
            "title": str(title).strip(),
            "url": str(url).strip(),
            "skill": skill,
            "duration_min": duration_minutes(row[2]),
        })
    return out


def load_questions(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [q for q in json.load(f) if q.get("domain") in MATH_DOMAINS]


def build(db: Session, videos: list[dict], questions: list[dict], dry_run: bool):
    by_skill = defaultdict(list)
    for v in videos:
        by_skill[v["skill"]].append(v)
    for vs in by_skill.values():
        vs.sort(key=lambda v: lesson_sort_key(v["title"]))

    q_by_skill = defaultdict(list)
    for q in questions:
        q_by_skill[q["skill"]].append(q)
    for qs in q_by_skill.values():
        qs.sort(key=lambda q: DIFF_RANK.get(str(q.get("difficulty", "")).lower(), 1))

    units = [(d, s) for d, s in SKILL_ORDER]
    if by_skill.get("FOUNDATIONS"):
        units.append(("Foundations", "FOUNDATIONS"))

    # Math questions already in the bank, grouped by skill. Reused instead of inserted.
    reusable = defaultdict(list)
    if db is not None:
        for q in db.query(models.Question).filter(models.Question.subject == "math").all():
            reusable[q.skill].append(q)
        for qs in reusable.values():
            qs.sort(key=lambda q: DIFF_RANK.get(str(q.difficulty.value if hasattr(q.difficulty, "value") else q.difficulty).lower(), 1))
        if reusable:
            print(f"reusing {sum(len(v) for v in reusable.values())} math questions already in the bank\n")

    if dry_run:
        print(f"{'UNIT':46} {'LESSONS':>8} {'QUESTIONS':>10}")
        for _, skill in units:
            print(f"{skill:46} {len(by_skill.get(skill, [])):>8} {len(q_by_skill.get(skill, [])):>10}")
        print(f"\ntotals: {len(units)} units, {sum(len(by_skill[s]) for _, s in units)} lessons, "
              f"{sum(len(q_by_skill.get(s, [])) for _, s in units)} questions")
        return

    course = models.Course(
        subject="math",
        course_type="test_prep",
        title="SAT Math",
        short_title="SAT Math",
        description=(
            "Every SAT math skill, taught on video and drilled with real test questions. "
            "Each lesson pairs a worked explanation with practice from the same skill."
        ),
        icon="",
        color="bg-[#6366f1]",
        price=0.0,
        skills=[s for _, s in units if s != "FOUNDATIONS"],
        grade_range="9–12",
        features=[
            "Video explanation in every lesson",
            "Real SAT questions grouped by skill",
            "Easy to hard within each lesson",
            "Full-length diagnostic assessment",
        ],
        image_emoji="",
        certificate_enabled=True,
    )
    db.add(course)
    db.flush()

    n_lessons = n_questions = 0
    for u_idx, (domain, skill) in enumerate(units):
        title = "Foundations & Review" if skill == "FOUNDATIONS" else skill
        unit = models.Unit(
            course_id=course.id,
            title=title,
            slug=slugify(f"{COURSE_SLUG}-{title}"),
            order_index=u_idx,
            description=f"{domain} — {title}" if skill != "FOUNDATIONS" else
                        "Pre-algebra groundwork. Optional, but the fastest fix if the SAT units feel shaky.",
        )
        db.add(unit)
        db.flush()

        vids = by_skill.get(skill, [])
        # Prefer questions already in the bank. The scraped set has usually been seeded
        # already, and inserting from JSON regardless would duplicate every one of them.
        existing = reusable.get(skill, [])
        skill_questions = existing or q_by_skill.get(skill, [])

        # A skill with questions but no video still needs somewhere to hold them.
        if not vids and skill_questions:
            vids = [{"title": f"{skill} — Practice", "url": None,
                     "duration_min": max(5, len(skill_questions) // 2), "skill": skill}]

        lessons = []
        for l_idx, v in enumerate(vids):
            blocks = []
            if v["url"]:
                blocks.append({"type": "video", "src": v["url"], "title": v["title"]})
            blocks.append({
                "type": "markdown",
                "content": (f"Watch the explanation, then work the questions below.\n\n"
                            f"**Skill:** {title}" if v["url"]
                            else f"Practice set for **{title}**. No video for this skill yet."),
            })
            lesson = models.Lesson(
                unit_id=unit.id,
                title=v["title"],
                slug=slugify(f"{v['title']}-{u_idx}-{l_idx}"),
                order_index=l_idx,
                content=f"{title} — {v['title']}",
                content_blocks=blocks,
                objectives=[f"Understand and apply: {title}"],
                duration_min=v["duration_min"],
                skills=[skill] if skill != "FOUNDATIONS" else ["Foundations"],
                difficulty="medium",
                prerequisite_lesson_id=lessons[-1].id if lessons else None,
            )
            db.add(lesson)
            db.flush()
            lessons.append(lesson)
            n_lessons += 1

        # Deal the skill's questions across its lessons round-robin, so each lesson
        # gets a spread of difficulties rather than one lesson hoarding all the easy ones.
        for q_idx, q in enumerate(skill_questions):
            lesson = lessons[q_idx % len(lessons)] if lessons else None

            if existing:
                # Attach through the many-to-many only. lesson_id/unit_id/course_id are
                # scalar FKs that may already point at another course's lesson; stealing
                # them would silently empty that course.
                if lesson:
                    lesson.questions.append(q)
                    if q.lesson_id is None:
                        q.lesson_id, q.unit_id, q.course_id = lesson.id, unit.id, course.id
                n_questions += 1
                continue

            question = models.Question(
                subject="math",
                grade_level=11,
                question_type="multiple-choice",
                prompt=str(q.get("question", "")),
                context=map_context(q.get("passage")),
                options=[f"{k}. {v}" for k, v in sorted((q.get("choices") or {}).items())],
                correct_answer=str(q.get("correct_answer", "")),
                skill=skill,
                explanation=build_explanation(q),
                review_status="published",
                difficulty=map_difficulty(q.get("difficulty")),
                source_test_id=q.get("_source_test_id") or q.get("test_id"),
                course_id=course.id,
                unit_id=unit.id,
                lesson_id=lesson.id if lesson else None,
            )
            db.add(question)
            if lesson:
                lesson.questions.append(question)
            n_questions += 1

        db.commit()
        print(f"  {title:46} {len(lessons):>3} lessons  {len(skill_questions):>4} questions")

    course.lesson_count = n_lessons
    db.commit()
    print(f"\ncourse {course.id}: {len(units)} units, {n_lessons} lessons, {n_questions} questions")


def reset(db: Session):
    course = db.query(models.Course).filter(models.Course.title == "SAT Math").first()
    while course:
        db.query(models.Question).filter(models.Question.course_id == course.id).delete()
        db.delete(course)  # units and lessons cascade
        db.commit()
        print(f"removed existing course {course.id}")
        course = db.query(models.Course).filter(models.Course.title == "SAT Math").first()


def main():
    ap = argparse.ArgumentParser()
    root = Path(__file__).parent.parent
    ap.add_argument("--videos", type=Path, default=root / "data" / "youtube_videos.xlsx")
    ap.add_argument("--questions", type=Path, default=root / "data" / "all_sat_questions.json")
    ap.add_argument("--reset", action="store_true", help="delete an existing SAT Math course first")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    args = ap.parse_args()

    for p in (args.videos, args.questions):
        if not p.exists():
            sys.exit(f"missing input: {p}")

    videos = load_videos(args.videos)
    questions = load_questions(args.questions)
    print(f"{len(videos)} teaching videos, {len(questions)} math questions\n")

    if args.dry_run:
        build(None, videos, questions, dry_run=True)
        return

    db = SessionLocal()
    try:
        if args.reset:
            reset(db)
        elif db.query(models.Course).filter(models.Course.title == "SAT Math").first():
            sys.exit("SAT Math already exists. Re-run with --reset to rebuild it.")
        build(db, videos, questions, dry_run=False)
    finally:
        db.close()


if __name__ == "__main__":
    main()
