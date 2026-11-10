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
et un jeu de test ; le contrôle de `A_dev` et `A_test` après extraction confirme que `N-CMAPSS_DS02-006.h5` suit ce
découpage (`docs/data.md`).

Un chiffre de la littérature n'entre dans `docs/resultats.md` que s'il provient d'une publication citée avec sa
référence complète et s'il utilise le même découpage.

## Conséquences
- DS02 compte deux modes de panne : HPT pour les moteurs 2, 5 et 10, HPT combiné au LPT pour les autres, moteurs de
  test compris. Son modèle reste entraîné sur ce seul fichier.
- DS02 sert à la comparaison : il n'apparaît que sur la page Modèle et ne fait pas partie des 65 moteurs de la page
  Flotte.
- Exception ponctuelle à la marge d'espace disque, autorisée par le propriétaire : l'extraction de DS02 seul a été
  lancée avec une marge de 10 Go au lieu de 15 Go, car il restait 15,4 Go libres pour un fichier de 2,45 Go. La marge
  par défaut du script reste 15 Go. Commande :
  `SSL_CERT_FILE="$(venv/bin/python -m certifi)" python -m scripts.download_ncmapss --only DS02 --margin-go 10`.
- La publication de référence définit le RMSE et le score NASA mais ne publie aucun résultat RUL chiffré : elle ne
  fournit donc pas de valeur à comparer. Les chiffres cités dans `docs/resultats.md` viennent du préprint
  arXiv:2003.00732v2, présenté comme tel, hors du tableau de nos résultats ; la version publiée en 2022 n'a pas pu
  être consultée.
- La RUL max de DS02 vaut 88 en dev et 75 en test : la règle sans plafond de l'ADR-008 s'applique.

## Sources
- Arias Chao, M. ; Kulkarni, C. ; Goebel, K. ; Fink, O. Aircraft Engine Run-to-Failure Dataset Under Real Flight
  Conditions for Prognostics and Diagnostics. Data 2021, 6, 5. https://doi.org/10.3390/data6010005
- Documentation de l'archive officielle : `Run_to_Failure_Simulation_Under_Real_Flight_Conditions_Dataset.pdf`.
- ADR-007, ADR-008.
