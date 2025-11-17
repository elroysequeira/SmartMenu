"""Database configuration and session management."""
from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path

# Database file path
DB_PATH = Path(__file__).parent.parent / "db.sqlite"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency for getting database session."""
    with Session(engine) as session:
        yield session

