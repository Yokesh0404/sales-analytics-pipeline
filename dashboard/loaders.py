"""Data loading for the dashboard: choose the data mode, load tables (cached), apply filters.

Two data modes:
- "db":       read the KPI tables from PostgreSQL (analytics schema). Used locally.
- "snapshot": read Parquet files from dashboard/data/ (made by src/export_snapshot.py).
              Used on Streamlit Cloud, which can't reach the laptop's database.

The mode comes from the setting DASHBOARD_DATA_MODE ("db", "snapshot" or "auto"),
read from an environment variable or Streamlit secrets. "auto" (the default) tries
the database and falls back to the snapshot if it can't connect.
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

DASHBOARD_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DASHBOARD_DIR.parent
SNAPSHOT_DIR = DASHBOARD_DIR / "data"

# Columns that hold dates, so we can convert them to real datetimes after loading.
DATE_COLUMNS = ["month", "cohort_month"]


# --- Settings and data mode -----------------------------------------------------

def get_setting(name, default=None):
    """Read a setting: environment variable first, then .streamlit/secrets.toml."""
    if os.getenv(name):
        return os.getenv(name)
    try:
        return st.secrets.get(name, default)
    except Exception:          # no secrets file at all -> just use the default
        return default


def get_engine():
    """Reuse the project's connection helper (src/db.py), which reads .env."""
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from db import get_engine as project_get_engine
    return project_get_engine()


@st.cache_data(ttl=600, show_spinner=False)
def resolve_mode():
    """Decide where data comes from. Returns (mode, reason). Re-checked every 10 minutes."""
    requested = str(get_setting("DASHBOARD_DATA_MODE", "auto")).lower()
    if requested == "snapshot":
        return "snapshot", "DASHBOARD_DATA_MODE=snapshot"
    try:
        with get_engine().connect() as conn:
            conn.exec_driver_sql("SELECT 1")          # cheap test query
        return "db", "connected to PostgreSQL"
    except Exception as error:
        # On Streamlit Cloud there is no .env and no reachable database, so we end up here.
        return "snapshot", f"database not reachable ({type(error).__name__}), using snapshot files"


# --- Loading tables ---------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner="Loading data...")
def load_table(name, mode):
    """Load one analytics table. Cached: the first call reads it, later calls are instant.

    `mode` is a parameter so the cache keeps db and snapshot results apart.
    """
    if mode == "db":
        df = pd.read_sql_table(name, get_engine(), schema="analytics")
    else:
        df = pd.read_parquet(SNAPSHOT_DIR / f"{name}.parquet")
    for column in DATE_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column])
    return df


def load(name):
    """Shortcut used by the pages: load a table in the current mode."""
    mode, _ = resolve_mode()
    return load_table(name, mode)


def snapshot_date():
    """When the snapshot files were exported (from manifest.json), or None."""
    try:
        manifest = json.loads((SNAPSHOT_DIR / "manifest.json").read_text(encoding="utf-8"))
        return manifest["exported_at"][:10]
    except Exception:
        return None


# --- Filters ------------------------------------------------------------------------

def apply_filters(df, category_column="category_name", month_column="month"):
    """Keep only rows matching the sidebar filters (stored in st.session_state).

    An empty state/category selection means "all".
    """
    start, end = st.session_state["filter_months"]
    keep = (df[month_column] >= pd.Timestamp(start)) & (df[month_column] <= pd.Timestamp(end))

    states = st.session_state.get("filter_states") or []
    if states and "customer_state" in df.columns:
        keep &= df["customer_state"].isin(states)

    categories = st.session_state.get("filter_categories") or []
    if categories and category_column in df.columns:
        keep &= df[category_column].isin(categories)

    return df[keep]


def filters_active():
    """True if the user narrowed state or category (used to label insights)."""
    return bool(st.session_state.get("filter_states") or st.session_state.get("filter_categories"))


# --- Formatting -----------------------------------------------------------------------

def brl(value):
    """Format Brazilian reais: R$ 15.42M, R$ 845.3K, R$ 152.40."""
    if value is None or pd.isna(value):
        return "–"
    if abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"R$ {value / 1_000:,.1f}K"
    return f"R$ {value:,.2f}"


def insight(text):
    """Grey caption under a chart with a Stage 6 finding (always about the full dataset)."""
    st.caption(f"💡 **Insight (full dataset):** {text}")
