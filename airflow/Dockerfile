# Our Airflow image = the official Airflow image + one extra Python environment
# for the pipeline code (pandas, SQLAlchemy 2, dbt).
FROM apache/airflow:3.3.2-python3.12

# Why a separate virtual environment?
# Airflow pins its own versions of many packages. Installing pandas/SQLAlchemy/dbt
# into Airflow's environment could break Airflow (or our scripts). In a separate venv
# they never clash, and it's the SAME requirements.txt we use on the laptop.
COPY requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/airflow/pipeline-venv \
 && PIP_USER=false /opt/airflow/pipeline-venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt
