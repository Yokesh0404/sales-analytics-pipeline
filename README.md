# Olist Sales Analytics Pipeline

An end-to-end data pipeline on the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce):
Python ingestion → data quality checks → dbt star schema → Airflow orchestration → Streamlit dashboard.

> 🚧 Work in progress. The full README (architecture, insights, screenshots, live link) comes in the final stage.

## Quick start (local)

```powershell
# 1. Create and activate a virtual environment
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your database credentials
copy .env.example .env   # then edit .env with your real password

# 4. Check the database connection
python src/check_connection.py
```

Download the Olist CSVs from Kaggle and place them in `data/raw/`.
