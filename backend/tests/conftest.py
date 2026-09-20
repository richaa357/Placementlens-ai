"""Test fixtures: an isolated in-memory-ish database seeded with the demo data."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database import get_db
from app.main import app
from app.models import Base
from app.seed import load_dataset, seed_database


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool, future=True
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="session")
def session_factory(engine):
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = factory()
    try:
        seed_database(db, load_dataset(get_settings().dataset_path))
    finally:
        db.close()
    return factory


@pytest.fixture
def db(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    # TestClient is used without its context manager on purpose: that skips the
    # lifespan hook, which would otherwise create/seed the real database file.
    yield TestClient(app)
    app.dependency_overrides.clear()
