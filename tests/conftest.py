import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base


@pytest.fixture
def session():
    DATABASE_URL = "sqlite:///:memory:"

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False
    )

    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="session")
def prepare_postgres_schema():
    import app.models
    from tests.reserve_db_session import engine

    Base.metadata.create_all(bind=engine)

