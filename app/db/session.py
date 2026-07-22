import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

engine = create_engine(
    DATABASE_URL,
    echo=SQL_ECHO
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()