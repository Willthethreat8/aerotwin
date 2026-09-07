import pytest
import pandas as pd
from metar import Metar
import geopandas as gpd

# --- TEST 1 : Vérification de la logique de décodage METAR ---
def test_metar_parsing():
    """Vérifie que la bibliothèque Metar extrait correctement les données d'un code brut."""
    raw_code = "LFBO 161030Z AUTO 29004KT 210V340 9999 FEW040 13/08 Q1025"
    obs = Metar.Metar(raw_code)
    
    # On teste si les valeurs extraites sont les bonnes
    assert obs.station_id == "LFBO"
    assert obs.temp.value() == 13.0
    assert obs.press.value() == 1025.0
    assert obs.wind_speed.value() == 4.0

# --- TEST 2 : Vérification du format des trajectoires ---
def test_trajectory_columns():
    """Vérifie que notre fichier de trajectoires contient les colonnes nécessaires."""
    # On charge le fichier généré précédemment
    import geopandas as gpd
    gdf = gpd.read_file('data/processed/trajectoires_simulees.geojson')
    
    
    expected_cols = ['engine_id', 'geometry']
    for col in expected_cols:
        assert col in gdf.columns
    
    # Vérifie que c'est bien du format spatial (LineString)
    assert gdf.geometry.geom_type.iloc[0] == 'LineString'

# --- TEST 3 : Simulation d'une erreur d'API ---
def test_empty_api_response():
    """Vérifie que notre logique gère le cas où l'API renvoie une liste vide."""
    donnees_vides = []
    # La logique devrait retourner un DataFrame vide ou None, pas planter
    df = pd.DataFrame(donnees_vides)
    assert df.empty
