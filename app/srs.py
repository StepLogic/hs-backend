from datetime import date, datetime, timedelta

from app import models


def score_to_quality(correct: bool, time_spent: int, difficulty: str) -> int:
    """Map correctness + time + difficulty to SM-2 quality [0..5]."""
    if not correct:
        return 0
    # Base quality for correct answer
    q = 3
    if difficulty == "hard":
        q += 1
    elif difficulty == "easy":
        q += 2
    else:
        q += 1
    # Time bonus/penalty: target ~30s per question
    if time_spent < 15:
        q += 1
    elif time_spent > 60:
        q -= 1
    return max(0, min(5, q))


def update_mastery(mastery: models.SkillMastery, quality: int) -> models.SkillMastery:
    """SM-2 update for a single review."""
    mastery.repetitions += 1

    # Update easiness factor (minimum 1.3)
    mastery.easiness = max(1.3, mastery.easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

    # Update interval
    if quality < 3:
        mastery.repetitions = 0
        mastery.interval_days = 1
    elif mastery.repetitions == 1:
        mastery.interval_days = 1
    elif mastery.repetitions == 2:
        mastery.interval_days = 6
    else:
        mastery.interval_days = int(round(mastery.easiness * mastery.interval_days))

    # Update due date
    mastery.due_date = date.today() + timedelta(days=mastery.interval_days)
    mastery.last_practiced = datetime.utcnow()

    # Update mastery score (weighted blend)
    # New score = 20% of quality * 20 (to get 0-100) + 80% of old score
    new_score = quality * 20
    mastery.mastery_score = int(0.2 * new_score + 0.8 * mastery.mastery_score)

    # Map mastery score to level
    if mastery.mastery_score >= 90:
        mastery.mastery_level = models.MasteryLevel.ADVANCED
    elif mastery.mastery_score >= 70:
        mastery.mastery_level = models.MasteryLevel.PROFICIENT
    elif mastery.mastery_score >= 50:
        mastery.mastery_level = models.MasteryLevel.DEVELOPING
    else:
        mastery.mastery_level = models.MasteryLevel.BEGINNER

    return mastery


def demo():
    """Self-check: print a 5-review schedule."""
    mastery = models.SkillMastery(
        student_id="demo",
        subject=models.Subject.MATH,
        skill="algebra",
        mastery_score=0,
        repetitions=0,
        easiness=2.5,
        interval_days=1,
        due_date=date.today(),
    )
    for day, quality in enumerate([3, 4, 3, 5, 4], start=1):
        update_mastery(mastery, quality)
        print(f"Day {day}: quality={quality}, score={mastery.mastery_score}, interval={mastery.interval_days}, due={mastery.due_date}")
    assert mastery.mastery_score > 0
    print("SRS demo passed")


if __name__ == "__main__":
    demo()
