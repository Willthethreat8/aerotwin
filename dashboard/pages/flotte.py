"""Page Flotte : état de chaque moteur à un cycle observé (ADR-009)."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).resolve().parents[2] / "data" / "dashboard"
SEUIL_CRITIQUE = 15
SEUIL_ATTENTION = 30
CYCLE_INITIAL = 60  # toutes les catégories de statut sont visibles à ce cycle
STATUTS = ["Critique", "Attention", "OK", "Déposé"]
COULEURS = {"OK": "#0a7d0a", "Attention": "#ec835a", "Critique": "#d03b3b", "Déposé": "#8a8983"}
FONDS = {"OK": "#c8ecc8", "Attention": "#fbdccd", "Critique": "#f3c6c6", "Déposé": "#e8e8e4"}


@st.cache_data
def charger(nom: str) -> pd.DataFrame:
    return pd.read_parquet(DATA / f"{nom}.parquet")


def etat_flotte(cycles: pd.DataFrame, observe: int) -> pd.DataFrame:
    """Une ligne par moteur : son état au cycle observé, ou Déposé si sa vie est plus courte."""
    moteurs = cycles.groupby(["ds_id", "fault_mode", "unit", "split"], as_index=False)["cycle"].max()
    moteurs = moteurs.rename(columns={"cycle": "panne"})
    a_ce_cycle = cycles.loc[cycles["cycle"] == observe, ["ds_id", "unit", "rul_pred", "hs"]]
    etat = moteurs.merge(a_ce_cycle, how="left", on=["ds_id", "unit"])
    etat["statut"] = pd.cut(
        etat["rul_pred"], bins=[float("-inf"), SEUIL_CRITIQUE, SEUIL_ATTENTION, float("inf")],
        right=False, labels=["Critique", "Attention", "OK"],
    ).astype(object).where(etat["rul_pred"].notna(), "Déposé")
    return etat


def repartition(etat: pd.DataFrame) -> go.Figure:
    fichiers = (etat["ds_id"] + " : " + etat["fault_mode"]).rename("fichier")
    comptes = pd.crosstab(fichiers, etat["statut"]).reindex(columns=STATUTS, fill_value=0).sort_index(ascending=False)
    fig = go.Figure([
        go.Bar(
            y=comptes.index, x=comptes[statut], name=statut, orientation="h",
            marker={"color": COULEURS[statut], "line": {"color": "#ffffff", "width": 2}},
            hovertemplate="%{y}<br>" + statut + " : %{x} moteurs<extra></extra>",
        )
        for statut in STATUTS
    ])
    fig.update_layout(
        barmode="stack", height=300, margin={"l": 120, "r": 10, "t": 30, "b": 50}, paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff", legend={"orientation": "h", "y": 1.12, "x": 0, "traceorder": "normal"},
        font={"color": "#52514e"},
    )
    fig.update_xaxes(title="Nombre de moteurs", gridcolor="#eeeeea", dtick=2)
    return fig


def tableau(etat: pd.DataFrame):
    ordre = etat["statut"].map({s: i for i, s in enumerate(STATUTS)})
    lignes = etat.assign(_ordre=ordre).sort_values(["_ordre", "rul_pred", "panne"])
    deposes = lignes["statut"] == "Déposé"
    vue = pd.DataFrame({
        "Fichier": lignes["ds_id"],
        "Mode de panne": lignes["fault_mode"],
        "Moteur": lignes["unit"],
        "Jeu": lignes["split"],
        # Le modèle peut prédire une RUL légèrement négative près de la panne
        "RUL prédite (cycles)": lignes["rul_pred"].clip(lower=0).round(0),
        "Statut": lignes["statut"].where(~deposes, "Déposé (panne au cycle " + lignes["panne"].astype(str) + ")"),
        "État de santé (hs)": lignes["hs"].map({1: "Sain", 0: "Dégradé"}).fillna(""),
    })
    return vue.style.format({"RUL prédite (cycles)": "{:.0f}"}, na_rep="").map(
        lambda valeur: f"background-color: {FONDS[valeur.split(' (')[0]]}; color: #0b0b0b", subset=["Statut"],
    )


cycles = charger("cycles")
cycles = cycles[cycles["in_fleet"]]

st.title("Flotte")

filtre_ds, filtre_mode, filtre_jeu = st.columns(3)
fichiers = filtre_ds.multiselect("Fichier", sorted(cycles["ds_id"].unique()), default=sorted(cycles["ds_id"].unique()))
modes = filtre_mode.multiselect(
    "Mode de panne", sorted(cycles["fault_mode"].unique()), default=sorted(cycles["fault_mode"].unique()),
)
jeux = filtre_jeu.multiselect("Jeu", ["dev", "test"], default=["dev", "test"])

selection = cycles[cycles["ds_id"].isin(fichiers) & cycles["fault_mode"].isin(modes) & cycles["split"].isin(jeux)]
if selection.empty:
    st.info("Aucun moteur ne correspond à ces filtres.")
    st.stop()

dernier = int(selection["cycle"].max())
observe = st.slider("Cycle observé", min_value=1, max_value=dernier, value=min(CYCLE_INITIAL, dernier))
etat = etat_flotte(selection, observe)

comptes = etat["statut"].value_counts()
for colonne, statut in zip(st.columns(4), STATUTS):
    colonne.metric(statut, int(comptes.get(statut, 0)))

st.plotly_chart(repartition(etat), theme=None, width="stretch")
st.dataframe(tableau(etat), hide_index=True, width="stretch", height=460)

st.caption(
    f"Statut selon la RUL prédite : Critique sous {SEUIL_CRITIQUE} cycles, Attention sous {SEUIL_ATTENTION} cycles, "
    "OK au-delà (ADR-009). Déposé : le moteur est arrivé à la panne avant le cycle observé. Moteurs dev : prédiction "
    "du modèle entraîné sans ce moteur. Moteurs test : prédiction du modèle final. L'état de santé hs est le label "
    "fourni par la simulation."
)
