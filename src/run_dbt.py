"""Run a dbt command with the database settings from .env.

dbt reads its credentials from environment variables (see dbt/profiles.yml),
but it doesn't read .env files by itself. This script loads .env first, then
passes your arguments straight to dbt.

Run from the project root:
    python src/run_dbt.py debug
    python src/run_dbt.py run
    python src/run_dbt.py test
    python src/run_dbt.py docs generate
"""
import sys
from pathlib import Path

from dbt.cli.main import dbtRunner
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DBT_DIR = PROJECT_ROOT / "dbt"

# Put POSTGRES_HOST, POSTGRES_PASSWORD, ... into the environment for dbt.
load_dotenv(PROJECT_ROOT / ".env")

# sys.argv[1:] = whatever you typed after the script name, e.g. ["run"].
args = sys.argv[1:] + ["--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)]

# dbtRunner runs dbt inside this Python process (same as typing `dbt ...`).
result = dbtRunner().invoke(args)

# Exit 0 on success, 1 on failure, so other tools (like Airflow) can tell.
sys.exit(0 if result.success else 1)
