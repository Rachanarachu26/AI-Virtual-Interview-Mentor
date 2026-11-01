"""Create all database tables. Run once to bootstrap an empty database.

Usage (from the backend/ directory):
    python -m app.database.init_db
"""
from app.database.database import Base, engine

# Importing the models package registers every model on Base.metadata.
import app.models  # noqa: F401


def init_db() -> None:
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done. All tables created.")


if __name__ == "__main__":
    init_db()
