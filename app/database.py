from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# Connection budget, not defaults. Measured on the managed database:
#   25 max_connections, 3 superuser-reserved, and 8 permanently held by
#   DigitalOcean's own agents (pg_cron, pghoard, pg_failover_slots, management-agent,
#   TimescaleDB launcher) -> roughly 14 actually available to this app.
# SQLAlchemy defaults to pool_size=5 + max_overflow=10 = 15 per process, and gunicorn
# runs 4 worker processes each with its own engine: a ceiling of 60. The app starved
# itself and left nothing for alembic or psql.
# 4 workers x (2 + 1) = 12, which fits under 14 with a slot spare for migrations.
_url = settings.sqlalchemy_database_url
# SQLite (tests) uses a SingletonThreadPool, which rejects these arguments outright.
_pool_args = (
    {}
    if _url.startswith("sqlite")
    else {
        "pool_size": 2,
        "max_overflow": 1,
        "pool_recycle": 1800,  # the managed DB drops idle connections; don't hand out dead ones
    }
)

engine = create_engine(_url, pool_pre_ping=True, **_pool_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
