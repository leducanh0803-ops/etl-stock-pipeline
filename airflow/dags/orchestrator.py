import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
from datetime import datetime, timedelta

sys.path.append('/opt/airflow/api-request')

def main_callable():
    from pipeline import main
    return main()

default_args = {
    'description': 'A DAG to schedule the stock market pipeline',
    'start_date': datetime(2026,5,31),
    'catch_up': False
}

dag = DAG(
    dag_id="stock_market_pipeline",
    default_args = default_args,
    schedule = timedelta(seconds=30)
)

with dag:
    task1 = PythonOperator(
        task_id = 'ingest_data',
        python_callable = main_callable
    )
    # task2 = DockerOperator(
    #     task_id = 'transform_data',
    #     image = 'ghcr.io/dbt-labs/dbt-postgres:1.9.latest',
    #     command = 'run',
    #     working_dir = '/usr/app',
    #     network_mode = 'new-project_my-network',
    #     mounts = [
    #         Mount(
    #             source='/home/leduc/repos/new-project/dbt/my_project',
    #             target='/usr/app',
    #             type='bind'
    #         ),
    #         Mount(
    #             source='/home/leduc/repos/new-project/dbt/profiles.yml',
    #             target='/root/.dbt/profiles.yml',
    #             type='bind'
    #         )
    #     ],
    #     docker_url = 'unix:///var/run/docker.sock',
    #     auto_remove = 'success'

    # )
    # task1 >> task2