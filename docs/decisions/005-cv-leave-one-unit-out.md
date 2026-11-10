# ADR-005 : Validation croisée leave-one-unit-out
Date : 2026-09-07
Statut : acceptée

## Contexte
Les cycles d'un même moteur sont fortement corrélés. Un split aléatoire par ligne place des cycles voisins du
même moteur en entraînement et en validation, ce qui surestime la performance. DS01 ne compte que 6 moteurs dev.

## Options envisagées
- KFold aléatoire sur les cycles.
- GroupKFold à k plis par moteur.
- Leave-one-unit-out : un pli par moteur dev.

## Décision
Leave-one-unit-out sur les moteurs dev, puis entraînement final sur tous les moteurs dev et évaluation sur les
moteurs test officiels.

## Conséquences
- Aucune fuite entre moteurs.
- Avec si peu de moteurs, les métriques varient fortement d'un moteur à l'autre : RMSE CV 18.47 contre 11.79 en
  test sur DS01. Les métriques doivent être publiées par moteur, avec l'écart-type (étape 3).
- Les prédictions hors échantillon de chaque moteur dev servent aussi au dashboard (étape 4).

## Sources
- Commit `c53fd57`, `src/train.py` (`cross_validate`).
