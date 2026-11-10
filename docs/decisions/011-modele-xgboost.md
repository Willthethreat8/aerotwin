# ADR-011 : Modèle XGBoost, hyperparamètres fixes, un modèle par fichier
Date : 2026-11-10
Statut : acceptée

## Contexte
Après l'agrégation par cycle (ADR-003), chaque fichier N-CMAPSS représente moins de 1 200 lignes et 9 à 15 moteurs,
dont 6 à 9 en développement. Les fichiers correspondent à des modes de panne et à des conditions d'exploitation
différents. Le projet vise une baseline honnête, pas la meilleure performance possible (ADR-006). Cet ADR documente
a posteriori des choix faits à partir de la phase 4.1.

## Options envisagées
- Modèle : régression linéaire ou forêt aléatoire, XGBoost, modèles séquentiels (exclus par l'ADR-003 et l'ADR-006).
  Aucune comparaison chiffrée entre algorithmes n'a été réalisée.
- Hyperparamètres : recherche par fichier, ou valeurs identiques fixées a priori. Avec 6 à 9 moteurs de développement,
  une recherche risque d'ajuster les paramètres à quelques moteurs.
- Portée : un modèle commun à plusieurs fichiers, ou un modèle par fichier. Mélanger les fichiers introduit un
  changement de domaine entre modes de panne.
- Variables : mesures brutes du cycle seules, ou ajout d'un historique glissant.

## Décision
- `XGBRegressor`, adapté aux relations non linéaires sur données tabulaires, sans mise à l'échelle, rapide sur ces
  volumes et fournissant une importance des variables.
- Mêmes hyperparamètres pour tous les fichiers, sans recherche : 300 arbres, profondeur 4, taux d'apprentissage 0,05,
  `subsample` et `colsample_bytree` à 0,8, graine 42.
- Un modèle par fichier, jamais d'entraînement sur plusieurs fichiers mélangés.
- Variables : moyenne, écart-type, minimum et maximum par cycle des conditions de vol (`W`) et des 14 capteurs
  (`X_s`), `Fc` en one-hot sur des catégories fixes, moyenne et écart-type glissants sur 5 cycles des moyennes de
  capteurs. La fenêtre glissante, calculée par moteur, ne regarde que le cycle courant et les précédents.

## Conséquences
- Les erreurs sont comparables entre fichiers, car seul le jeu de données change.
- Le modèle reste une baseline : ni l'algorithme, ni les hyperparamètres, ni la fenêtre de 5 cycles ne sont optimisés.
- Un modèle entraîné sur un fichier ne dit rien de sa généralisation à un autre mode de panne.
- DS02 mêle deux modes de panne dans un même fichier (ADR-010) : son modèle reste entraîné sur ce seul fichier.

## Sources
- `src/train.py`, `src/features.py`, `src/config.py`, `docs/resultats.md`.
- `ROADMAP.md`, section « Règle anti-pool ».
- ADR-003, ADR-004, ADR-005, ADR-006, ADR-010.
