from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


def get_database_url() -> str:
    return settings.database_url


connect_args = {}
if get_database_url().startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(get_database_url(), connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.database.models import Base

    Base.metadata.create_all(bind=engine)
