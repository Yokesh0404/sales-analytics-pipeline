"""Run data quality checks against the `raw` schema in PostgreSQL.

Run from the project root:
    python src/quality_checks.py

How it works:
- Every check is a SQL query that COUNTS the rows breaking one rule.
- 0 bad rows  -> PASS.
- >0 bad rows -> the check's severity: FAIL (broken keys, pipeline must stop)
                 or WARN (smaller issue, report it and carry on).
- Results go to the console, logs/quality.log and the table quality.check_results.
- The script exits with code 1 if any check FAILs, so Airflow can stop the pipeline.
"""
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine

# --- Settings -----------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

RAW_TABLES = [
    "customers", "geolocation", "order_items", "order_payments", "order_reviews",
    "orders", "products", "sellers", "product_category_name_translation",
]

# The order statuses we expect to see in the Olist data.
KNOWN_ORDER_STATUSES = [
    "created", "approved", "invoiced", "processing",
    "shipped", "delivered", "canceled", "unavailable",
]


# --- Logging --------------------------------------------------------------------

def setup_logging():
    """Send log messages to both the console and logs/quality.log."""
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_DIR / "quality.log", encoding="utf-8"),
        ],
    )
    return logging.getLogger("quality")


# --- Check builders -------------------------------------------------------------
# Each function below returns one check as a dictionary:
#   name     - short description shown in the report
#   table    - the raw table being checked
#   severity - status to give the check if it finds bad rows ("FAIL" or "WARN")
#   sql      - a query that returns ONE number: how many rows break the rule

def row_count_check(table):
    """FAIL if the table is empty (returns 1 'bad row' when count is 0)."""
    return {
        "name": "row_count > 0",
        "table": table,
        "severity": "FAIL",
        "sql": f"SELECT CASE WHEN count(*) = 0 THEN 1 ELSE 0 END FROM raw.{table}",
    }


def not_null_check(table, column, severity):
    """Count rows where the column is empty."""
    return {
        "name": f"not_null({column})",
        "table": table,
        "severity": severity,
        "sql": f"SELECT count(*) FROM raw.{table} WHERE {column} IS NULL",
    }


def unique_check(table, columns, severity="FAIL"):
    """Count extra rows that repeat a key that should be unique.

    Group by the key, keep only groups with more than 1 row, and add up
    (rows in group - 1). E.g. one order_id appearing 3 times = 2 extra rows.
    """
    key = ", ".join(columns)
    return {
        "name": f"unique({key})",
        "table": table,
        "severity": severity,
        "sql": f"""
            SELECT coalesce(sum(n - 1), 0)
            FROM (SELECT count(*) AS n FROM raw.{table}
                  GROUP BY {key} HAVING count(*) > 1) AS dupes
        """,
    }


def foreign_key_check(child, column, parent, parent_column, severity="FAIL"):
    """Count 'orphan' rows: the child's key has no matching row in the parent."""
    return {
        "name": f"fk({column} -> {parent})",
        "table": child,
        "severity": severity,
        "sql": f"""
            SELECT count(*) FROM raw.{child} AS c
            WHERE c.{column} IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM raw.{parent} AS p
                              WHERE p.{parent_column} = c.{column})
        """,
    }


def parses_as_check(table, column, data_type):
    """Count values that can't be converted to the given type.

    All raw columns are text, so we check they CAN be converted before dbt
    converts them in stage 4. pg_input_is_valid() needs PostgreSQL 16 or newer.
    """
    return {
        "name": f"parses_as_{data_type}({column})",
        "table": table,
        "severity": "WARN",
        "sql": f"""
            SELECT count(*) FROM raw.{table}
            WHERE {column} IS NOT NULL
              AND NOT pg_input_is_valid({column}, '{data_type}')
        """,
    }


def custom_check(name, table, severity, where_clause):
    """Count rows matching a 'bad row' condition written in SQL."""
    return {
        "name": name,
        "table": table,
        "severity": severity,
        "sql": f"SELECT count(*) FROM raw.{table} WHERE {where_clause}",
    }


# --- The list of checks ---------------------------------------------------------

def build_checks():
    checks = []

    # 1. Every raw table has data.
    for table in RAW_TABLES:
        checks.append(row_count_check(table))

    # 2. Primary keys: not null and unique. Broken keys = FAIL.
    primary_keys = {
        "orders": ["order_id"],
        "customers": ["customer_id"],
        "products": ["product_id"],
        "sellers": ["seller_id"],
        "order_items": ["order_id", "order_item_id"],
    }
    for table, columns in primary_keys.items():
        for column in columns:
            checks.append(not_null_check(table, column, "FAIL"))
        checks.append(unique_check(table, columns))
    # review_id looks like a key, but we only WARN: we'll handle it in dbt.
    checks.append(unique_check("order_reviews", ["review_id"], severity="WARN"))

    # 3. Foreign keys resolve (no orphan rows). Broken keys = FAIL.
    checks += [
        foreign_key_check("order_items", "order_id", "orders", "order_id"),
        foreign_key_check("order_items", "product_id", "products", "product_id"),
        foreign_key_check("order_items", "seller_id", "sellers", "seller_id"),
        foreign_key_check("orders", "customer_id", "customers", "customer_id"),
        foreign_key_check("order_payments", "order_id", "orders", "order_id"),
        foreign_key_check("order_reviews", "order_id", "orders", "order_id"),
        # Category names without an English translation: annoying, not broken.
        foreign_key_check("products", "product_category_name",
                          "product_category_name_translation", "product_category_name",
                          severity="WARN"),
    ]

    # 4. Nulls in important non-key columns. These are WARN.
    checks += [
        not_null_check("orders", "order_purchase_timestamp", "WARN"),
        not_null_check("orders", "customer_id", "FAIL"),  # needed to join to customers
        not_null_check("order_items", "price", "WARN"),
        not_null_check("order_items", "product_id", "FAIL"),
        not_null_check("order_items", "seller_id", "FAIL"),
        not_null_check("products", "product_category_name", "WARN"),
    ]

    # 5. Text values can be converted to proper types (done for real in dbt).
    timestamp_columns = {
        "orders": ["order_purchase_timestamp", "order_approved_at",
                   "order_delivered_carrier_date", "order_delivered_customer_date",
                   "order_estimated_delivery_date"],
        "order_items": ["shipping_limit_date"],
    }
    for table, columns in timestamp_columns.items():
        for column in columns:
            checks.append(parses_as_check(table, column, "timestamp"))
    checks += [
        parses_as_check("order_items", "price", "numeric"),
        parses_as_check("order_items", "freight_value", "numeric"),
        parses_as_check("order_payments", "payment_value", "numeric"),
    ]

    # 6. Values in a sensible range. These are WARN.
    statuses = ", ".join(f"'{s}'" for s in KNOWN_ORDER_STATUSES)
    checks += [
        custom_check("price >= 0", "order_items", "WARN", "price::numeric < 0"),
        custom_check("freight_value >= 0", "order_items", "WARN", "freight_value::numeric < 0"),
        custom_check("payment_value >= 0", "order_payments", "WARN", "payment_value::numeric < 0"),
        custom_check("review_score between 1 and 5", "order_reviews", "WARN",
                     "review_score IS NULL OR review_score NOT IN ('1', '2', '3', '4', '5')"),
        custom_check("order_status in known set", "orders", "WARN",
                     f"order_status IS NULL OR order_status NOT IN ({statuses})"),
    ]

    # 7. Date logic.
    checks += [
        custom_check("delivered_date >= purchase_date", "orders", "WARN",
                     "order_delivered_customer_date::timestamp < order_purchase_timestamp::timestamp"),
        custom_check("delivered orders have delivery date", "orders", "WARN",
                     "order_status = 'delivered' AND order_delivered_customer_date IS NULL"),
    ]
    return checks


# --- Running the checks -----------------------------------------------------------

def run_checks(engine, checks, run_at, logger):
    """Run every check and return a list of result dictionaries."""
    results = []
    with engine.connect() as conn:
        for check in checks:
            try:
                total_rows = conn.execute(text(f"SELECT count(*) FROM raw.{check['table']}")).scalar()
                failing_rows = conn.execute(text(check["sql"])).scalar()
                status = "PASS" if failing_rows == 0 else check["severity"]
            except Exception:
                # The query itself broke (e.g. table missing or a value that can't be
                # converted). We can't trust the data, so the check FAILs.
                logger.exception("Check errored: %s on %s", check["name"], check["table"])
                conn.rollback()  # a failed query blocks the connection until we roll back
                total_rows, failing_rows, status = None, None, "FAIL"

            # Percentage of the table's rows that broke the rule.
            failing_pct = None
            if total_rows and failing_rows is not None:
                failing_pct = round(100 * failing_rows / total_rows, 3)

            results.append({
                "run_at": run_at,
                "check_name": check["name"],
                "table_name": check["table"],
                "status": status,
                "failing_rows": failing_rows,
                "total_rows": total_rows,
                "failing_pct": failing_pct,
            })
            logger.info("%-4s | %-20s | %-45s | failing rows: %s",
                        status, check["table"], check["name"], failing_rows)
    return results


def save_results(engine, results):
    """Append this run's results to quality.check_results (keeps history of every run)."""
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS quality"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS quality.check_results (
                run_at       timestamptz NOT NULL,
                check_name   text        NOT NULL,
                table_name   text        NOT NULL,
                status       text        NOT NULL,
                failing_rows bigint,
                total_rows   bigint,
                failing_pct  numeric
            )
        """))
        # Passing a list of dictionaries inserts one row per dictionary.
        conn.execute(text("""
            INSERT INTO quality.check_results
                (run_at, check_name, table_name, status, failing_rows, total_rows, failing_pct)
            VALUES
                (:run_at, :check_name, :table_name, :status, :failing_rows, :total_rows, :failing_pct)
        """), results)


def main():
    logger = setup_logging()
    engine = get_engine()
    run_at = datetime.now(timezone.utc)  # one timestamp for the whole run

    checks = build_checks()
    logger.info("Running %d data quality checks on schema 'raw'", len(checks))
    results = run_checks(engine, checks, run_at, logger)
    save_results(engine, results)

    # Print a readable summary table to the console.
    summary = pd.DataFrame(results).drop(columns="run_at")
    print("\n" + summary.to_string(index=False) + "\n")

    counts = summary["status"].value_counts()
    logger.info("Summary: %d PASS, %d WARN, %d FAIL",
                counts.get("PASS", 0), counts.get("WARN", 0), counts.get("FAIL", 0))

    if counts.get("FAIL", 0) > 0:
        logger.error("Data quality FAILED - stopping the pipeline")
        sys.exit(1)  # non-zero exit code tells Airflow the task failed
    logger.info("Data quality passed (warnings, if any, are in the report above)")


if __name__ == "__main__":
    main()
