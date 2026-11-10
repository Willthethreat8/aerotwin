# ADR-009 : Streamlit + export Parquet
Date : 2026-11-10
Statut : acceptée

## Contexte
Le projet doit se conclure par un dashboard déployable sur Streamlit Community Cloud, qui n'a pas accès aux `.h5`
(hors Git) et doit démarrer en moins de 5 secondes. Les trajectoires N-CMAPSS vont toutes jusqu'à la panne : au
dernier cycle, la RUL réelle vaut 0 pour chaque moteur.

## Options envisagées
- Lire le HDF5 depuis le dashboard : impossible à déployer, trop lent.
- Export Parquet par `src/export_dashboard.py`, lu par Streamlit avec `st.cache_data`.
- Page Flotte au dernier cycle : tous les moteurs seraient Critique, la page ne dirait rien.
- Page Flotte à un cycle observé choisi par curseur.
- Seuils sur la RUL prédite brute : avec un RMSE test de 23.60, les moteurs DS04 passeraient en Critique trop tard.
- Seuils sur une RUL prudente, qui retire l'erreur du modèle propre à chaque fichier.

## Décision
Streamlit multipage natif (`dashboard/app.py`, `dashboard/pages/`), Plotly, données lues uniquement depuis
`data/dashboard/*.parquet`. DS02 n'apparaît que sur la page Modèle (ADR-010).

La page Flotte affiche, pour chaque moteur, son état au cycle observé : RUL prédite, statut, `hs`. Un moteur dont la
vie est plus courte que ce cycle est marqué « Déposé (panne au cycle N) ». Le curseur démarre au cycle 60 : les
durées de vie vont de 59 à 100 cycles (médiane 80), et les quatre statuts y sont visibles (26 Critique, 25 Attention,
13 OK, 1 Déposé).

Les seuils s'appliquent à une estimation prudente : RUL prédite moins le RMSE test moyen par moteur de son fichier
(`summary.parquet`). Critique si cette valeur passe sous 15 cycles, Attention sous 30, OK au-delà. En maintenance, une
alerte manquée coûte plus qu'une fausse alerte : le seuil tient donc compte de l'erreur du modèle propre à chaque mode
de panne, de 11.55 à 23.60 cycles selon le fichier. Ces seuils sont simples et non calibrés sur un coût opérationnel.

## Conséquences
- Le dashboard fonctionne sans `.h5` ni secret ; `dashboard/requirements.txt` limite le déploiement à quatre paquets.
- Démarrage mesuré en local : environ 2,5 s entre le lancement du serveur et le rendu de la page Flotte.
- Les alertes sont plus nombreuses : au cycle 60, 26 moteurs sont Critique contre 10 avec la RUL prédite brute. La
  règle accepte davantage de fausses alertes pour en manquer moins.
- Le RMSE test sert de marge d'affichage. Il est estimé sur les moteurs test eux-mêmes : la règle n'a pas été évaluée
  séparément.
- Le statut reflète une prédiction du modèle sur données simulées, pas une décision de maintenance.

## Sources
- `docs/resultats.md`, `docs/data.md`.
- ADR-006, ADR-010.
