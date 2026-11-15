"""Database connection helper.

Reads the PostgreSQL credentials from the .env file, so no password is ever
written in the code. Every other script imports get_engine() from here,
which means the connection logic lives in exactly one place.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Load the KEY=value lines from .env into environment variables.
# Variables that are already set (for example inside Docker) are NOT overwritten.
load_dotenv()


def get_engine():
    """Build and return a SQLAlchemy engine for the Olist database."""
    # URL.create builds the connection string for us and safely escapes
    # special characters in the password (like @ or #).
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.environ["POSTGRES_DB"],
    )
    # The engine does not connect yet; it connects when we first use it.
    return create_engine(url)
