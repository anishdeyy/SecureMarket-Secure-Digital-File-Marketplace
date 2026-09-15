from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from app.config import settings

# SQLite needs check_same_thread=False, PostgreSQL doesn't
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///./"):
        rel_path = url[len("sqlite:///./"):]
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abs_db_path = os.path.abspath(os.path.join(backend_dir, rel_path))
        url = f"sqlite:///{abs_db_path.replace(os.sep, '/')}"
    engine = create_engine(url, connect_args=connect_args)
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
