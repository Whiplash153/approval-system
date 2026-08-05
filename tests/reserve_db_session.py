import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.engine import make_url


load_dotenv()

APPLICATION_DATABASE_URL = os.getenv("DATABASE_URL")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not APPLICATION_DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not set")

application_database_name = make_url(APPLICATION_DATABASE_URL).database
test_database_name = make_url(TEST_DATABASE_URL).database

if application_database_name == test_database_name:
    raise RuntimeError(
        "TEST_DATABASE_URL must point to a separate database"
    )

engine = create_engine(TEST_DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)
