from typing import Optional

from sqlalchemy.orm import Session

from app.database import get_db as _get_db

# Re-export get_db so endpoints import dependencies from a single location
get_db = _get_db


def get_current_user() -> Optional[dict]:
    """Placeholder dependency until JWT / session auth is wired up."""
    return None
