# ADR-003 : Agrégation 1 Hz vers cycle le plus tôt possible
Date : 2026-09-07
Statut : acceptée

## Contexte
DS01 contient environ 4,9 millions de lignes en dev et 2,7 millions en test, à 1 Hz. La RUL et l'état de santé
`hs` ne changent qu'une fois par cycle de vol.

## Options envisagées
- Garder la résolution 1 Hz et travailler par fenêtres glissantes.
- Agréger chaque cycle juste après l'extraction (moyenne, écart-type, min, max par variable).

## Décision
Agréger en une ligne par `(unit, cycle)` dans `aggregate_to_cycles`, immédiatement après la lecture du HDF5.
`Fc`, `hs` et `RUL` prennent la première valeur du cycle.

## Conséquences
- Quelques milliers de lignes par fichier : entraînement, tests et export légers.
- L'information intra-vol (phases montée, croisière, descente) n'est conservée que via les statistiques.
- Les modèles séquentiels à 1 Hz (LSTM, CNN) sont exclus, ce qui est cohérent avec le périmètre (ADR-006).

## Sources
- Commit `5df8433`, `src/transform.py`.
