# ADR-004 : Exclusion des groupes X_v et T (fuite de données)
Date : 2026-09-07
Statut : acceptée

## Contexte
Le HDF5 N-CMAPSS fournit `W` (conditions de vol), `X_s` (capteurs physiques), `X_v` (capteurs virtuels),
`T` (paramètres de santé θ), `A` (auxiliaires) et `Y` (RUL). `T` décrit directement la dégradation simulée et
`X_v` est calculé par le modèle thermodynamique : aucun des deux n'est mesurable sur un moteur réel.

## Options envisagées
- Utiliser tous les groupes.
- Se limiter à ce qu'un exploitant mesure : `W`, `X_s`, `Fc`.

## Décision
Le modèle n'utilise que `W`, `X_s` et `Fc`. `X_v` et `T` ne sont pas lus. `unit`, `cycle`, `hs` et `RUL` sont
exclus des variables explicatives (`split_features_target`).

## Conséquences
- Les performances reflètent un usage réaliste.
- `hs` reste disponible pour l'affichage (bascule sain vers dégradé) mais n'entre pas dans le modèle.

## Sources
- `src/features.py`, `src/extract.py`.
- Arias Chao et al., Data, 6(1):5, 2021.
