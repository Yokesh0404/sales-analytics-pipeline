"""Quick check that Python can reach PostgreSQL using the settings in .env.

Run from the project root:
    python src/check_connection.py
"""
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from db import get_engine

try:
    engine = get_engine()
    # "with" opens a connection and closes it automatically afterwards.
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar()
    print("Connected! PostgreSQL version:")
    print(version)
except OperationalError as error:
    # Most common causes: wrong password, database not created, Postgres not running.
    print("Could not connect to PostgreSQL. Check the values in your .env file.")
    print("Details:", error)
