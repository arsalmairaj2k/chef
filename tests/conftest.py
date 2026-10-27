import os
from dotenv import load_dotenv

load_dotenv()

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

import app.models  # ensure all models are registered
from app.database.base import Base
from app.database.session import get_db
from app.main import app as fastapi_app
from app.ai.providers import set_llm_provider
from app.ai.providers.fake import FakeLLMProvider


@pytest.fixture(autouse=True)
def default_fake_provider():
    """Ensure standard tests run offline and deterministically with FakeLLMProvider."""
    set_llm_provider(FakeLLMProvider())
    yield
    set_llm_provider(None)


@pytest.fixture(scope="session")
def test_engine():
    """Create an in-memory SQLite engine configured for strict foreign keys."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine) -> Session:
    """Yield a transactional database session rolled back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()



@pytest.fixture(scope="function")
def client(db_session: Session):
    """FastAPI TestClient with get_db dependency overridden."""
    from fastapi.testclient import TestClient

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(fastapi_app)
    yield test_client
    fastapi_app.dependency_overrides.clear()

