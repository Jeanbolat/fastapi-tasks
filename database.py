import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    DATABASE_URL = database_url
else:
    DATABASE_URL = URL.create(
        drivername="postgresql+psycopg",
        username="postgres",
        password=os.environ["DATABASE_PASSWORD"],
        host=os.getenv("DATABASE_HOST", "localhost"),
        port=5432,
        database="tasks_db",
    )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass