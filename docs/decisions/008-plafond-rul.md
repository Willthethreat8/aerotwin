# ADR-008 : Suppression du plafond RUL
Date : 2026-11-09
Statut : acceptée

## Contexte
Le plafond à 125, repris des pratiques C-MAPSS, était appliqué à la cible. Sur N-CMAPSS, les RUL max relevées dans
`docs/data.md` valent de 84 à 99 en dev et de 89 à 98 en test pour DS01 et DS03 à DS07. La comparaison capped /
uncapped de la phase 4.2 donnait exactement le même RMSE : elle ne comparait rien.

## Options envisagées
- Garder le plafond à 125 : sans effet sur ces fichiers, et laisse croire à un réglage qui n'existe pas.
- Choisir un plafond plus bas : nouvel hyperparamètre, hors du principe « pas de recherche d'hyperparamètres ».
- Supprimer le plafond pour tous les fichiers.

## Décision
Pas de plafond : `RUL_CAP = None` dans `src/train.py`, même règle pour tous les fichiers.

## Conséquences
- Le modèle prédit la RUL brute et les métriques sont calculées contre la RUL réelle.
- La comparaison capped / uncapped disparaît de `src/train.py`.
- DS02, ajouté par l'ADR-010, suit la même règle : sa RUL max vaut 88 en dev et 75 en test.

## Sources
- `docs/data.md`.
- Commit `8019140` (comparaison de la phase 4.2).
