"""Load every Olist CSV from data/raw/ into the `raw` schema in PostgreSQL.

Run from the project root:
    python src/ingest.py

Safe to re-run: each table is fully replaced, so running it twice gives
the same result (this is called being "idempotent").
"""
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine

# --- Settings -----------------------------------------------------------------

# Build paths from this file's location, so the script works no matter
# which folder you run it from (important later for Airflow).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
LOG_DIR = PROJECT_ROOT / "logs"

SCHEMA = "raw"       # PostgreSQL schema the tables go into
CHUNK_SIZE = 10_000  # rows sent to the database per batch, keeps memory use low


# --- Logging --------------------------------------------------------------------

def setup_logging():
    """Send log messages to both the console and logs/ingestion.log."""
    LOG_DIR.mkdir(exist_ok=True)  # create logs/ if it doesn't exist yet
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(),  # console
            logging.FileHandler(LOG_DIR / "ingestion.log", encoding="utf-8"),  # file
        ],
    )
    return logging.getLogger("ingest")


# --- Helpers --------------------------------------------------------------------

def table_name_from_file(csv_path):
    """Turn 'olist_orders_dataset.csv' into 'orders'.

    Files without the prefix/suffix keep their name, e.g.
    'product_category_name_translation.csv' -> 'product_category_name_translation'.
    """
    name = csv_path.stem  # file name without the .csv extension
    name = name.removeprefix("olist_")
    name = name.removesuffix("_dataset")
    return name


def load_csv(engine, csv_path, table_name, loaded_at):
    """Read one CSV and write it to raw.<table_name>. Returns the row count."""
    # dtype=str keeps every value exactly as it appears in the file.
    # Example: zip code "01037" would lose its leading zero if read as a number.
    # Converting to proper types (dates, numbers) is the job of dbt in stage 4.
    df = pd.read_csv(csv_path, dtype=str)

    # Record when this data was loaded, useful for tracing problems later.
    df["_loaded_at"] = loaded_at

    # engine.begin() opens a transaction: if anything fails, the whole write is
    # rolled back and the previous version of the table stays untouched.
    with engine.begin() as conn:
        df.to_sql(
            name=table_name,
            con=conn,
            schema=SCHEMA,
            if_exists="replace",  # drop and recreate the table -> safe to re-run
            index=False,          # don't write pandas' row numbers as a column
            chunksize=CHUNK_SIZE, # insert in batches instead of all at once
        )
    return len(df)


# --- Main -----------------------------------------------------------------------

def main():
    logger = setup_logging()
    engine = get_engine()

    # Create the raw schema the first time; does nothing if it already exists.
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))

    csv_files = sorted(RAW_DATA_DIR.glob("*.csv"))
    if not csv_files:
        logger.error("No CSV files found in %s", RAW_DATA_DIR)
        sys.exit(1)

    logger.info("Starting ingestion of %d files into schema '%s'", len(csv_files), SCHEMA)

    # One timestamp for the whole run, so all tables from this run share it.
    loaded_at = datetime.now(timezone.utc)
    failed_files = []

    for csv_path in csv_files:
        table_name = table_name_from_file(csv_path)
        start = time.perf_counter()
        try:
            row_count = load_csv(engine, csv_path, table_name, loaded_at)
            seconds = time.perf_counter() - start
            logger.info(
                "Loaded %-45s -> %s.%-35s %9d rows in %5.1fs",
                csv_path.name, SCHEMA, table_name, row_count, seconds,
            )
        except Exception:
            # Log the full error, remember the file, and move on to the next one.
            logger.exception("FAILED to load %s", csv_path.name)
            failed_files.append(csv_path.name)

    if failed_files:
        logger.error("Ingestion finished with %d failure(s): %s", len(failed_files), failed_files)
        sys.exit(1)  # non-zero exit code tells Airflow (stage 5) the task failed

    logger.info("Ingestion finished successfully: %d tables loaded", len(csv_files))


# Only run main() when this file is executed directly, not when it is imported.
if __name__ == "__main__":
    main()
