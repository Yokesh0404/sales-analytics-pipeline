"""Export the dashboard's KPI tables from PostgreSQL to small Parquet files.

Why: Streamlit Community Cloud can't reach the PostgreSQL on this laptop.
The dashboard's "snapshot" mode reads these files instead.

Only AGGREGATED tables are exported. A safety check refuses any table that
contains customer-level columns, so no personal data ends up in the files.

Run from the project root (after `dbt run`):
    python src/export_snapshot.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from db import get_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "dashboard" / "data"

# The analytics tables the dashboard needs. All are aggregates built by dbt.
TABLES = [
    "kpi_sales_cube",        # revenue by month x state x category
    "kpi_order_cube",        # order KPIs by month x state x main category x delivery status
    "kpi_seller_cube",       # seller KPIs by seller x month x state x category
    "kpi_repeat_customers",  # single row
    "kpi_cohort_retention",  # cohort x months-since-first-purchase
]

# Columns that would identify a customer or an order. If any table has one,
# the export stops: snapshot files must never contain personal data.
FORBIDDEN_COLUMNS = {"customer_id", "customer_unique_id", "order_id", "zip_code_prefix",
                     "city", "review_id", "comment_title", "comment_message"}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    manifest = {"exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tables": {}}

    for table in TABLES:
        df = pd.read_sql_table(table, engine, schema="analytics")

        # Safety check: no customer-level columns allowed.
        bad_columns = FORBIDDEN_COLUMNS & set(df.columns)
        if bad_columns:
            print(f"REFUSED {table}: contains personal/row-level columns {sorted(bad_columns)}")
            sys.exit(1)

        path = OUTPUT_DIR / f"{table}.parquet"
        df.to_parquet(path, index=False)   # Parquet = compressed, keeps column types
        size_kb = path.stat().st_size / 1024
        manifest["tables"][table] = {"rows": len(df), "size_kb": round(size_kb, 1)}
        print(f"exported analytics.{table:<22} {len(df):>7,} rows  {size_kb:>7.1f} KB")

    # A small file recording when the snapshot was taken (shown in the dashboard).
    (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    total_kb = sum(t["size_kb"] for t in manifest["tables"].values())
    print(f"done: {len(TABLES)} tables, {total_kb:.0f} KB total -> {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
