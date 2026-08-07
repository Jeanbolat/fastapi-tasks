import os

from dotenv import load_dotenv

load_dotenv()
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

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