"""Test de fumée : chaque page du dashboard se charge sans erreur."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

DASHBOARD = Path(__file__).resolve().parents[1] / "dashboard"


@pytest.mark.parametrize("script", ["app.py", "pages/flotte.py", "pages/moteur.py", "pages/modele.py"])
def test_page_loads(script):
    at = AppTest.from_file(str(DASHBOARD / script), default_timeout=60).run()
    assert not at.exception
