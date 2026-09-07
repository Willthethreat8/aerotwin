"""Flow Prefect : pipeline N-CMAPSS DS01 de bout en bout.

À écrire EN DERNIER, quand extract/transform/load fonctionnent et sont testés.
Prefect s'ajoute en décorant tes fonctions — c'est tout l'intérêt.

    pip install prefect   (et l'ajouter à requirements.txt)

Lancement : python -m src.pipelines.flow_ds01
"""
from prefect import flow, task

from src import extract, load, transform

# TODO :
# 1. Wrapper chaque étape dans une @task (retries=2 sur l'extract météo —
#    les appels réseau échouent, c'est le cas d'usage n°1 des retries)
# 2. Un @flow qui enchaîne : read_ncmapss -> aggregate_to_cycles -> drop_constant_columns
#    -> add_rolling_features -> load_dataframe
#    + fetch_weather_history -> load_dataframe
#    + generate_trajectories -> load_geodataframe
# 3. if __name__ == "__main__": lancer le flow


@task(retries=2, retry_delay_seconds=10)
def extract_weather_task(start_date: str, end_date: str):
    raise NotImplementedError


@flow(name="aerotwin-ds01")
def ds01_pipeline():
    raise NotImplementedError


if __name__ == "__main__":
    ds01_pipeline()
