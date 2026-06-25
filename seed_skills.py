#!/usr/bin/env python3
"""Seed skill taxonomy from existing question skills."""

import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base
from app import models


def seed():
    engine = create_engine(settings.sqlalchemy_database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        # Map old subject values to new ones for existing questions
        subject_map = {
            "math": models.Subject.MATH,
            "reading": models.Subject.ENGLISH_LANGUAGE_ARTS,
            "comprehension": models.Subject.ENGLISH_LANGUAGE_ARTS,
        }

        rows = db.query(models.Question.skill, models.Question.subject).distinct().all()
        added = 0
        for skill, subject in rows:
            mapped_subject = subject_map.get(subject.value if hasattr(subject, "value") else subject, models.Subject.MATH)
            existing = db.query(models.SkillTaxonomy).filter_by(subject=mapped_subject, skill=skill).first()
            if existing:
                continue
            db.add(models.SkillTaxonomy(subject=mapped_subject, skill=skill, description=None))
            added += 1

        db.commit()
        print(f"Seeded {added} skills")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
