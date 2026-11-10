"""Page Modèle : erreurs par fichier et par moteur, résidus, importance des variables."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).resolve().parents[2] / "data" / "dashboard"
BLEU, ENCRE, GRIS = "#2a78d6", "#52514e", "#8a8983"
COULEUR_JEU = {"dev": GRIS, "test": BLEU}


@st.cache_data
def charger(nom: str) -> pd.DataFrame:
    return pd.read_parquet(DATA / f"{nom}.parquet")


def style(fig: go.Figure, hauteur: int = 380, gauche: int = 80) -> go.Figure:
    fig.update_layout(
        height=hauteur, margin={"l": gauche, "r": 10, "t": 30, "b": 70}, paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font={"color": ENCRE}, legend={"orientation": "h", "y": 1.08, "x": 0},
    )
    fig.update_xaxes(gridcolor="#eeeeea")
    fig.update_yaxes(gridcolor="#eeeeea")
    return fig


def nom_fichier(ds_id: str, mode: str, in_fleet: bool) -> str:
    return f"{ds_id}<br>{mode}" + ("" if in_fleet else "<br>(comparaison)")


def erreurs_par_fichier(summary: pd.DataFrame) -> go.Figure:
    series = [("CV (leave-one-unit-out)", "cv", GRIS), ("Test", "test", BLEU)]
    fig = go.Figure([
        go.Bar(
            x=summary["fichier"], y=summary[f"{cle}_rmse_mean"], name=nom, marker={"color": couleur, "line": {"color": "#ffffff", "width": 2}},
            error_y={"type": "data", "array": summary[f"{cle}_rmse_std"], "color": ENCRE, "thickness": 1},
            hovertemplate="%{x}<br>" + nom + " : %{y:.2f} ± %{error_y.array:.2f}<extra></extra>",
        )
        for nom, cle, couleur in series
    ])
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="RMSE moyen par moteur (cycles)", rangemode="tozero")
    return style(fig)


def erreurs_par_moteur(per_unit: pd.DataFrame, ordre: list[str]) -> go.Figure:
    fig = go.Figure([
        # Les boîtes sont invisibles : ces traces vides donnent ses pastilles à la légende
        go.Scatter(x=[None], y=[None], mode="markers", name=jeu, marker={"color": couleur, "size": 9})
        for jeu, couleur in COULEUR_JEU.items()
    ] + [
        go.Box(
            x=g["fichier"], y=g["rmse"], name=jeu, boxpoints="all", pointpos=0, jitter=0.35, fillcolor="rgba(0,0,0,0)", showlegend=False,
            line={"width": 0}, marker={"color": COULEUR_JEU[jeu], "size": 9, "line": {"color": "#ffffff", "width": 1}},
            text="Moteur " + g["unit"].astype(str), hoveron="points", hovertemplate="%{x}<br>%{text} : %{y:.2f}<extra>" + jeu + "</extra>",
        )
        for jeu, g in per_unit.groupby("split")
    ])
    fig.update_layout(boxmode="group")
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=ordre)
    fig.update_yaxes(title="RMSE du moteur (cycles)", rangemode="tozero")
    return style(fig)


def residus(predictions: pd.DataFrame) -> go.Figure:
    fig = go.Figure([
        go.Scatter(
            x=g["rul_true"], y=g["rul_pred"] - g["rul_true"], mode="markers", name=jeu,
            marker={"color": COULEUR_JEU[jeu], "size": 8, "opacity": 0.55},
            hovertemplate="RUL réelle %{x}<br>Résidu %{y:.1f}<extra>" + jeu + "</extra>",
        )
        for jeu, g in predictions.groupby("split")
    ])
    fig.add_hline(y=0, line={"color": ENCRE, "width": 1})
    fig.update_xaxes(title="RUL réelle (cycles)")
    fig.update_yaxes(title="Prédite moins réelle (cycles)")
    return style(fig, 420, 70)


def importances(table: pd.DataFrame) -> go.Figure:
    top = table.nlargest(15, "importance").sort_values("importance")
    fig = go.Figure(go.Bar(
        x=top["importance"], y=top["feature"], orientation="h", marker={"color": BLEU, "line": {"color": "#ffffff", "width": 2}},
        hovertemplate="%{y} : %{x:.3f}<extra></extra>",
    ))
    fig.update_xaxes(title="Importance (gain relatif)")
    return style(fig, 420, 190)


cycles = charger("cycles")
per_unit = charger("per_unit")
summary = charger("summary")
importance = charger("importance")

summary = summary.assign(fichier=[nom_fichier(*r) for r in zip(summary["ds_id"], summary["fault_mode"], summary["in_fleet"])])
summary = summary.sort_values("test_rmse_mean", ascending=False)
per_unit = per_unit.assign(fichier=[nom_fichier(*r) for r in zip(per_unit["ds_id"], per_unit["fault_mode"], per_unit["in_fleet"])])

st.title("Modèle")

st.subheader("Erreur par fichier")
st.plotly_chart(erreurs_par_fichier(summary), theme=None, width="stretch")
st.caption("Fichiers classés du plus difficile au plus facile en test. Barres d'erreur : écart-type entre moteurs.")

st.subheader("Erreur par moteur")
st.plotly_chart(erreurs_par_moteur(per_unit, summary["fichier"].tolist()), theme=None, width="stretch")

st.subheader("Détail par fichier")
ds_id = st.selectbox("Fichier", sorted(summary["ds_id"]), format_func=lambda d: summary.set_index("ds_id").loc[d, "fichier"].replace("<br>", " "))
gauche, droite = st.columns(2)
gauche.markdown("**Résidus par cycle**")
gauche.plotly_chart(residus(cycles[cycles["ds_id"] == ds_id]), theme=None, width="stretch")
droite.markdown("**15 variables les plus importantes (modèle final)**")
droite.plotly_chart(importances(importance[importance["ds_id"] == ds_id]), theme=None, width="stretch")

with st.container(border=True):
    st.markdown(
        "**Limites**\n\n"
        "- Données simulées (N-CMAPSS) : aucune validation sur des données réelles.\n"
        "- Peu de moteurs par mode de panne (3 à 6 en test) : les moyennes par fichier sont sensibles à un seul moteur.\n"
        "- DS02 sert uniquement à la comparaison à la littérature et ne fait pas partie de la flotte ; "
        "il est le seul fichier à mêler deux modes de panne."
    )
