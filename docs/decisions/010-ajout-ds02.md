# ADR-010 : Ajout de DS02 pour comparaison à la littérature
Date : 2026-11-09
Statut : acceptée

## Contexte
L'ADR-007 écartait DS02 pour rester dans le périmètre minimal. Les autres fichiers ne permettent pas de se situer
par rapport aux travaux publiés, qui utilisent DS02 comme référence. Le propriétaire revient donc sur ce point.

## Options envisagées
- Conserver l'ADR-007, sans point de comparaison externe.
- Ajouter DS02 avec un découpage maison : résultats non comparables.
- Ajouter DS02 avec le découpage de la publication de référence, uniquement pour comparaison.

## Décision
DS01 et DS03 à DS07 restent retenus comme dans l'ADR-007, avec un modèle par fichier. DS02 s'y ajoute uniquement
pour la comparaison à la littérature.

Découpage de DS02 : six moteurs d'entraînement (2, 5, 10, 16, 18, 20) et trois moteurs de test (11, 14, 15), tel
qu'indiqué par Arias Chao et al. (2021, légende de la figure 3). Chaque fichier distingue un jeu de développement
et un jeu de test ; `A_dev` et `A_test` serviront à contrôler après extraction que le fichier suit ce découpage.

Un chiffre de la littérature n'entre dans `docs/resultats.md` que s'il provient d'une publication citée avec sa
référence complète et s'il utilise le même découpage.

## Conséquences
- DS02 compte deux modes de panne : HPT pour les moteurs 2, 5 et 10, HPT combiné au LPT pour les autres, moteurs de
  test compris. Son modèle reste entraîné sur ce seul fichier.
- DS02 sert à la comparaison et ne fait pas partie des 65 moteurs de la page Flotte.
- La publication de référence définit le RMSE et le score NASA mais ne publie aucun résultat RUL chiffré : elle ne
  fournit donc pas de valeur à comparer.
- La RUL max de DS02 reste à relever pour vérifier la règle de l'ADR-008.

## Sources
- Arias Chao, M. ; Kulkarni, C. ; Goebel, K. ; Fink, O. Aircraft Engine Run-to-Failure Dataset Under Real Flight
  Conditions for Prognostics and Diagnostics. Data 2021, 6, 5. https://doi.org/10.3390/data6010005
- Documentation de l'archive officielle : `Run_to_Failure_Simulation_Under_Real_Flight_Conditions_Dataset.pdf`.
- ADR-007, ADR-008.
