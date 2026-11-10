"""Point d'entrée du dashboard AeroTwin.

Lancement depuis la racine du dépôt : streamlit run dashboard/app.py
"""
import streamlit as st

st.set_page_config(page_title="AeroTwin", layout="wide")

st.navigation([
    st.Page("pages/flotte.py", title="Flotte", default=True),
    st.Page("pages/moteur.py", title="Moteur"),
    st.Page("pages/modele.py", title="Modèle"),
]).run()
