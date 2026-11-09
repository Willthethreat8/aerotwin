# ADR-007 : Jeux de données retenus
Date : 2026-11-09
Statut : acceptée

## Contexte
DS01 seul compte 10 moteurs (6 dev, 4 test) et un seul mode de panne : les métriques sont dominées par la variance
entre moteurs (ADR-005). L'archive officielle N-CMAPSS contient dix fichiers : DS01 à DS07, DS08a, DS08c, DS08d.

## Options envisagées
- Rester sur DS01.
- DS01 et DS03 à DS07 : un mode de panne par fichier, 65 moteurs.
- Ajouter DS02, benchmark de la littérature (HPT + LPT, dans la même archive).
- Ajouter DS08a, DS08c, DS08d : plusieurs composants dégradés à la fois.

## Décision
DS01 et DS03 à DS07, un modèle par fichier. DS02 est écarté pour rester dans le périmètre minimal, bien qu'il
soit présent dans l'archive. DS08a, DS08c et DS08d sont écartés (modes multiples, hors périmètre).

| Fichier | Moteurs dev / test | Composant(s) dégradé(s) |
|---|---|---|
| DS01 | 6 / 4 | HPT |
| DS03 | 9 / 6 | HPT + LPT |
| DS04 | 6 / 4 | Fan |
| DS05 | 6 / 4 | HPC |
| DS06 | 6 / 4 | LPC + HPC |
| DS07 | 6 / 4 | LPT |

Téléchargement uniquement depuis la source officielle par `python -m scripts.download_ncmapss` : l'archive
(15,76 Go) est vérifiée en taille, `data_set.zip` est lu sans être écrit sur disque, seuls les six `.h5` retenus
sont extraits, avec contrôle CRC et SHA-256 consignés dans `docs/data.md`. Le fichier DS01 déjà présent a été
comparé à la version officielle : SHA-256 identique, fichier conservé.

## Conséquences
- `read_ncmapss(ds_id=...)` résout le fichier par motif et ajoute `ds_id` et `fault_mode`.
- Les RUL max relevées vont de 84 à 99 selon les fichiers (`docs/data.md`) : base de la décision sur le
  plafond RUL (ADR-008).
- Aucun résultat comparable à la littérature DS02 : ce n'est pas l'objectif.
- Environ 18 Go de `.h5` en local, hors Git.

## Sources
- NASA PCoE Prognostics Data Repository, « Turbofan Engine Degradation Simulation Data Set-2 ».
- Arias Chao et al., Data, 6(1):5, 2021.
- `docs/data.md`.
