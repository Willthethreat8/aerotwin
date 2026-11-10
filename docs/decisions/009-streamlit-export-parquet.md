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

## Décision
Streamlit multipage natif (`dashboard/app.py`, `dashboard/pages/`), Plotly, données lues uniquement depuis
`data/dashboard/*.parquet`. DS02 n'apparaît que sur la page Modèle (ADR-010).

La page Flotte affiche, pour chaque moteur, son état au cycle observé : RUL prédite, statut, `hs`. Un moteur dont la
vie est plus courte que ce cycle est marqué « Déposé (panne au cycle N) ». Le curseur démarre au cycle 60 : les
durées de vie vont de 59 à 100 cycles (médiane 80), et les quatre statuts y sont visibles.

Seuils appliqués à la RUL prédite, identiques pour tous les fichiers : Critique sous 15 cycles, Attention sous 30,
OK au-delà. Le RMSE test moyen par moteur vaut de 11.55 à 14.66 sur cinq des six fichiers de la flotte : sous
15 cycles, la RUL prédite n'est plus nettement supérieure à l'erreur typique du modèle. Le seuil de 30 en est environ
le double et laisse une marge d'alerte. Ces seuils sont simples et non calibrés sur un coût opérationnel.

## Conséquences
- Le dashboard fonctionne sans `.h5` ni secret ; `dashboard/requirements.txt` limite le déploiement à quatre paquets.
- Démarrage mesuré en local : environ 2,5 s entre le lancement du serveur et le rendu de la page Flotte.
- DS04 (Fan) a un RMSE test moyen de 23.60 : avec les mêmes seuils, ses moteurs passent en Critique trop tard
  par rapport à l'erreur du modèle. La page Modèle montre cet écart.
- Le statut reflète une prédiction du modèle sur données simulées, pas une décision de maintenance.

## Sources
- `docs/resultats.md`, `docs/data.md`.
- ADR-006, ADR-010.
