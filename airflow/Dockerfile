FROM apache/airflow:2.7.2

USER airflow

# Install Snowflake + AWS providers and dependencies
RUN pip install --no-cache-dir \
    apache-airflow-providers-snowflake==5.0.0 \
    apache-airflow-providers-amazon==8.7.0 \
    snowflake-connector-python \
    pandas
