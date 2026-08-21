from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=(settings.app_env == "development"),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
