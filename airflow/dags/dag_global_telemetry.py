from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import pandas as pd 

default_args = {
    'owner' : 'Aseel Al-Qazqzy',
    'depends_on_past': False,  # if last hour's run failed, do not freeze today's run. Let each hour to try to execute independently.
    'email_on_failure' : False ,
    'email_on_retry' : False,
    "retries": 2, # try twice if there an API blips or a networking request drops momentarily.
    "retry_delay": timedelta(minutes=5)
}