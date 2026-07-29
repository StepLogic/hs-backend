#!/usr/bin/env python3
"""
Export all fetched SAT questions to well-formatted Markdown files.
Organized by skill/domain for easy reading.
"""
import json
import re
import html
from pathlib import Path
from collections import defaultdict


def escape_latex(text: str) -> str:
    """Escape LaTeX math so it renders nicely in Markdown (code blocks)."""
    if not text:
        return ""
    # Wrap inline math $...$ with backticks for markdown compatibility
    text = re.sub(r'\$([^$]+?)\$', r'`\1`', text)
    # Wrap display math $$...$$ with triple backticks
    text = re.sub(r'\$\$(.+?)\$\$', r'```\n\1\n```', text, flags=re.DOTALL)
    return text


def clean_text(text: str) -> str:
    """Basic text cleaning for markdown."""
    if not text:
        return ""
    # Unescape HTML entities
    text = html.unescape(text)
    # Escape LaTeX
    text = escape_latex(text)
    return text.strip()


def format_choices(choices: dict) -> str:
    """Format answer choices as markdown list."""
    if not choices:
        return ""
    lines = []
    for key in sorted(choices.keys()):
        label = key.upper() if len(key) == 1 else key
        text = clean_text(str(choices[key]))
        lines.append(f"- **{label}.** {text}")
    return "\n".join(lines)


def format_distractors(distractor_explanation) -> str:
    """Format distractor explanations."""
    if not distractor_explanation:
        return ""
    if isinstance(distractor_explanation, list):
        items = distractor_explanation
    else:
        items = [distractor_explanation]
    lines = []
    for item in items:
        text = clean_text(str(item))
        if text:
            lines.append(f"- {text}")
    return "\n".join(lines) if lines else ""


def question_to_markdown(q: dict, number: int) -> str:
    """Convert a single question dict to markdown text."""
    lines = []

    # Question header with ID
    qid = q.get("id", "unknown")
    lines.append(f"### Question {number} (ID: `{qid}`)")
    lines.append("")

    # Metadata
    skill = q.get("skill", "Unknown Skill")
    domain = q.get("domain", "Unknown Domain")
    difficulty = q.get("difficulty", "Unknown")
    test_id = q.get("test_id", "")
    is_math = q.get("is_math", False)
    status = q.get("status", "")

    lines.append(f"**Skill:** {skill}  ")
    lines.append(f"**Domain:** {domain}  ")
    lines.append(f"**Difficulty:** {difficulty}  ")
    if test_id:
        lines.append(f"**Test ID:** `{test_id}`  ")
    if status:
        lines.append(f"**Status:** {status}  ")
    if is_math:
        lines.append(f"**Type:** Math  ")
    lines.append("")

    # Passage / Context
    passage = q.get("passage")
    if passage:
        lines.append("> **Passage:**")
        lines.append("> ")
        passage_text = clean_text(str(passage))
        # Quote each line
        for para in passage_text.split("\n"):
            lines.append(f"> {para}")
        lines.append("")

    # Question prompt
    question_text = clean_text(str(q.get("question", "")))
    if question_text:
        lines.append(f"**Question:** {question_text}")
        lines.append("")

    # Choices
    choices = q.get("choices", {})
    if choices:
        lines.append("**Choices:**")
        lines.append("")
        lines.append(format_choices(choices))
        lines.append("")

    # Correct Answer
    correct = q.get("correct_answer", "")
    lines.append(f"**Correct Answer:** `{correct}`")
    lines.append("")

    # Explanation
    explanation = q.get("explanation")
    if explanation:
        lines.append("**Explanation:**")
        lines.append("")
        lines.append(clean_text(str(explanation)))
        lines.append("")

    # Distractor explanations
    distractors = q.get("distractor_explanation")
    if distractors:
        lines.append("**Why other choices are wrong:**")
        lines.append("")
        lines.append(format_distractors(distractors))
        lines.append("")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def group_questions(questions: list) -> dict:
    """Group questions by skill, then by test_id."""
    groups = defaultdict(lambda: defaultdict(list))
    for q in questions:
        skill = q.get("skill", "Unknown Skill")
        test_id = q.get("test_id", "ungrouped")
        groups[skill][test_id].append(q)
    return groups


def generate_single_markdown(questions: list, output_path: Path):
    """Generate one giant markdown file with all questions."""
    lines = []
    lines.append("# SAT Practice Questions - Complete Collection")
    lines.append("")
    lines.append(f"**Total Questions:** {len(questions)}")
    lines.append("")
    lines.append("This document contains all SAT practice questions scraped from the Bloom Academy platform.")
    lines.append("Each question includes the prompt, answer choices, correct answer, explanation, and distractor analysis.")
    lines.append("")
    lines.append("---")
    lines.append("")

    groups = group_questions(questions)

    for skill in sorted(groups.keys()):
        lines.append(f"## {skill}")
        lines.append("")

        for test_id in sorted(groups[skill].keys()):
            test_questions = groups[skill][test_id]
            lines.append(f"### Test: `{test_id}` ({len(test_questions)} questions)")
            lines.append("")

            for i, q in enumerate(test_questions, 1):
                lines.append(question_to_markdown(q, i))

        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Written: {output_path}")


def generate_by_skill(questions: list, output_dir: Path):
    """Generate separate markdown files per skill."""
    output_dir.mkdir(parents=True, exist_ok=True)
    groups = group_questions(questions)

    for skill in sorted(groups.keys()):
        safe_name = re.sub(r'[^\w\s-]', '', skill).strip().replace(' ', '_').lower()
        filepath = output_dir / f"{safe_name}.md"

        lines = []
        lines.append(f"# {skill}")
        lines.append("")
        total_for_skill = sum(len(tq) for tq in groups[skill].values())
        lines.append(f"**Total Questions:** {total_for_skill}")
        lines.append("")
        lines.append("---")
        lines.append("")

        for test_id in sorted(groups[skill].keys()):
            test_questions = groups[skill][test_id]
            lines.append(f"## Test: `{test_id}` ({len(test_questions)} questions)")
            lines.append("")

            for i, q in enumerate(test_questions, 1):
                lines.append(question_to_markdown(q, i))

        filepath.write_text("\n".join(lines), encoding="utf-8")
        print(f"  Written: {filepath}")


def generate_by_test(questions: list, output_dir: Path):
    """Generate separate markdown files per test_id."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tests = defaultdict(list)
    for q in questions:
        tid = q.get("test_id", "unknown")
        tests[tid].append(q)

    for test_id in sorted(tests.keys()):
        safe_name = re.sub(r'[^\w\s-]', '', str(test_id)).strip().replace(' ', '_').lower()
        filepath = output_dir / f"{safe_name}.md"

        lines = []
        lines.append(f"# Test: `{test_id}`")
        lines.append("")
        lines.append(f"**Total Questions:** {len(tests[test_id])}")
        lines.append("")
        lines.append("---")
        lines.append("")

        for i, q in enumerate(tests[test_id], 1):
            lines.append(question_to_markdown(q, i))

        filepath.write_text("\n".join(lines), encoding="utf-8")
        print(f"  Written: {filepath}")


def main():
    data_file = Path(__file__).parent.parent / "data" / "sat_questions" / "all_sat_questions.json"
    if not data_file.exists():
        print(f"Error: Data file not found at {data_file}")
        print("Run fetch_sat_questions.py first.")
        return

    print(f"Loading questions from {data_file}...")
    with open(data_file, "r", encoding="utf-8") as f:
        questions = json.load(f)
    print(f"Loaded {len(questions)} questions.")

    output_base = Path(__file__).parent.parent / "data" / "sat_questions" / "markdown_export"
    output_base.mkdir(parents=True, exist_ok=True)

    # 1. Single combined file
    print("\nGenerating single combined markdown file...")
    single_file = output_base / "all_sat_questions.md"
    generate_single_markdown(questions, single_file)

    # 2. By skill
    print("\nGenerating markdown files grouped by skill...")
    by_skill_dir = output_base / "by_skill"
    generate_by_skill(questions, by_skill_dir)

    # 3. By test
    print("\nGenerating markdown files grouped by test...")
    by_test_dir = output_base / "by_test"
    generate_by_test(questions, by_test_dir)

    print(f"\n=== EXPORT COMPLETE ===")
    print(f"Output directory: {output_base}")
    print(f"  - Single file: {single_file}")
    print(f"  - By skill: {by_skill_dir}")
    print(f"  - By test: {by_test_dir}")


if __name__ == "__main__":
    main()
