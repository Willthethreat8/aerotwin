# ADR-002 : Abandon de C-MAPSS FD001 au profit de N-CMAPSS
Date : 2026-09-07
Statut : acceptée

## Contexte
La phase 0 utilisait C-MAPSS FD001 : un seul régime de vol, trois réglages abstraits, une ligne par cycle.
Ce jeu ne reflète pas des conditions de vol réelles et la RUL doit être reconstruite.

## Options envisagées
- Rester sur FD001 (ou FD002 à FD004).
- Passer à N-CMAPSS (2021), simulé à partir de profils de vol commerciaux enregistrés, 1 Hz, RUL et état de santé
  fournis.

## Décision
Passer à N-CMAPSS, en commençant par le fichier DS01 (dégradation HPT). Les notebooks 01 à 04 et le code FD001
sont retirés.

## Conséquences
- Volume nettement plus élevé (environ 2,8 Go pour DS01) : agrégation nécessaire (ADR-003).
- Les résultats obtenus sur FD001, dont la référence RMSE 36.89 obtenue en split aléatoire, ne sont pas
  comparables et ne sont plus cités.

## Sources
- Commit `5df8433`.
- M. Arias Chao, C. Kulkarni, K. Goebel, O. Fink, « Aircraft Engine Run-to-Failure Dataset under Real Flight
  Conditions for Prognostics and Diagnostics », Data, 6(1):5, 2021.
- A. Saxena, K. Goebel, D. Simon, N. Eklund, « Damage Propagation Modeling for Aircraft Engine Run-to-Failure
  Simulation », PHM 2008.
