"""Page Moteur : capteurs et RUL d'un moteur au fil des cycles."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

DATA = Path(__file__).resolve().parents[2] / "data" / "dashboard"
BLEU, ENCRE, GRIS = "#2a78d6", "#52514e", "#8a8983"
CAPTEURS = {
    "T24_mean": "Température totale sortie LPC (R)",
    "T30_mean": "Température totale sortie HPC (R)",
    "T48_mean": "Température totale sortie HPT (R)",
    "T50_mean": "Température totale sortie LPT (R)",
    "P15_mean": "Pression totale conduit de dérivation (psia)",
    "P2_mean": "Pression totale entrée soufflante (psia)",
    "P21_mean": "Pression totale sortie soufflante (psia)",
    "P24_mean": "Pression totale sortie LPC (psia)",
    "Ps30_mean": "Pression statique sortie HPC (psia)",
    "P40_mean": "Pression totale sortie chambre de combustion (psia)",
    "P50_mean": "Pression totale sortie LPT (psia)",
    "Nf_mean": "Régime soufflante (tr/min)",
    "Nc_mean": "Régime corps (tr/min)",
    "Wf_mean": "Débit de carburant (pps)",
}
PAR_DEFAUT = ["T50_mean", "T48_mean", "Nc_mean", "Wf_mean"]


@st.cache_data
def charger(nom: str) -> pd.DataFrame:
    return pd.read_parquet(DATA / f"{nom}.parquet")


def style(fig: go.Figure, hauteur: int) -> go.Figure:
    fig.update_layout(
        height=hauteur, margin={"l": 80, "r": 10, "t": 40, "b": 50}, paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font={"color": ENCRE}, hovermode="x unified",
    )
    fig.update_xaxes(gridcolor="#eeeeea")
    fig.update_yaxes(gridcolor="#eeeeea")
    return fig


def courbe_rul(moteur: pd.DataFrame, bascule: int) -> go.Figure:
    fig = go.Figure([
        go.Scatter(x=moteur["cycle"], y=moteur["rul_true"], name="RUL réelle", line={"color": GRIS, "width": 2, "dash": "dash"}),
        go.Scatter(x=moteur["cycle"], y=moteur["rul_pred"], name="RUL prédite", line={"color": BLEU, "width": 2}),
    ])
    fig.add_vline(x=bascule, line={"color": ENCRE, "width": 1, "dash": "dot"},
                  annotation_text=f"Bascule sain vers dégradé (cycle {bascule})", annotation_position="top right")
    fig.update_layout(legend={"orientation": "h", "y": -0.2, "x": 0})
    fig.update_xaxes(title="Cycle")
    fig.update_yaxes(title="RUL (cycles)")
    return style(fig, 380)


def courbes_capteurs(moteur: pd.DataFrame, choisis: list[str], bascule: int) -> go.Figure:
    lignes = (len(choisis) + 1) // 2
    fig = make_subplots(rows=lignes, cols=2, shared_xaxes=True, subplot_titles=[CAPTEURS[c] for c in choisis],
                        vertical_spacing=0.32 / lignes)
    for i, capteur in enumerate(choisis):
        ligne, colonne = i // 2 + 1, i % 2 + 1
        fig.add_trace(
            go.Scatter(x=moteur["cycle"], y=moteur[capteur], line={"color": BLEU, "width": 2}, showlegend=False,
                       name=capteur.removesuffix("_mean")),
            row=ligne, col=colonne,
        )
        fig.add_vline(x=bascule, row=ligne, col=colonne, line={"color": ENCRE, "width": 1, "dash": "dot"})
    fig.update_annotations(font={"size": 13, "color": ENCRE})
    fig.update_xaxes(title="Cycle", row=lignes)
    return style(fig, 300 * lignes)


cycles = charger("cycles")
per_unit = charger("per_unit")
cycles = cycles[cycles["in_fleet"]]

st.title("Moteur")

modes = cycles.drop_duplicates("ds_id").set_index("ds_id")["fault_mode"]
choix_ds, choix_moteur = st.columns(2)
ds_id = choix_ds.selectbox("Fichier", sorted(modes.index), format_func=lambda d: f"{d} : {modes[d]}")
unit = choix_moteur.selectbox("Moteur", sorted(cycles.loc[cycles["ds_id"] == ds_id, "unit"].unique()))

moteur = cycles[(cycles["ds_id"] == ds_id) & (cycles["unit"] == unit)].sort_values("cycle")
erreurs = per_unit[(per_unit["ds_id"] == ds_id) & (per_unit["unit"] == unit)].iloc[0]
bascule = int(moteur.loc[moteur["hs"] == 0, "cycle"].min())

for colonne, (titre, valeur) in zip(st.columns(5), [
    ("Jeu", erreurs["split"]),
    ("Panne au cycle", int(moteur["cycle"].max())),
    ("Bascule au cycle", bascule),
    ("RMSE (cycles)", f"{erreurs['rmse']:.1f}"),
    ("MAE (cycles)", f"{erreurs['mae']:.1f}"),
]):
    colonne.metric(titre, valeur)

st.subheader("RUL prédite et RUL réelle")
st.plotly_chart(courbe_rul(moteur, bascule), theme=None, width="stretch")

st.subheader("Capteurs (moyenne par cycle)")
choisis = st.multiselect("Capteurs affichés", list(CAPTEURS), default=PAR_DEFAUT, format_func=CAPTEURS.get)
if choisis:
    st.plotly_chart(courbes_capteurs(moteur, choisis, bascule), theme=None, width="stretch")
else:
    st.info("Sélectionner au moins un capteur.")

st.caption(
    "Les cycles sont des vols de durée variable, ce qui explique la dispersion des capteurs d'un cycle à l'autre. "
    "La bascule correspond au premier cycle où le label de simulation hs vaut dégradé."
)
