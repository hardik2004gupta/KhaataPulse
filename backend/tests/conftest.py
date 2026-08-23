"""
Shared pytest fixtures for KhaataPulse test suite.
Uses SQLite in-memory for speed; PostgreSQL-specific behaviour is covered by
migration smoke tests that require a live database.
"""
import pytest
from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
# Register all ORM models with Base.metadata
import app.db.models  # noqa: F401


@pytest.fixture(scope="session")
def engine():
    """Session-scoped in-memory SQLite engine with all tables created once."""
    eng = create_engine("sqlite:///:memory:", echo=False)

    # Enable FK enforcement in SQLite (off by default)
    @sa_event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    """Function-scoped session wrapped in a transaction that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
