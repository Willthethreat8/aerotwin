# Données N-CMAPSS

Source : NASA Prognostics Center of Excellence, Prognostics Data Repository, « Turbofan Engine Degradation Simulation Data Set-2 » (`https://phm-datasets.s3.amazonaws.com/NASA/17.+Turbofan+Engine+Degradation+Simulation+Data+Set+2.zip`). Fichiers générés par `python -m scripts.download_ncmapss`.

## Fichiers

| Fichier | Taille (octets) | SHA-256 |
|---|---|---|
| N-CMAPSS_DS01-005.h5 | 2873351432 | `3abdcee2a3c8136e8880e5d43ac8cdf12ab9f7f3ab37145f23b24c11335afbed` |
| N-CMAPSS_DS02-006.h5 | 2450472504 | `47971a68b239ecb756833218a95d68ded6eb7e63ee84e86671c8b188de1ca765` |
| N-CMAPSS_DS03-012.h5 | 3693395776 | `f67cc4bd0cf927f09eb8e0198bd62c777e1c6213177cfc46d81cc43bba52c333` |
| N-CMAPSS_DS04.h5 | 3752493952 | `2b58cbb78497679fadafe0761203b2ae3b0e4e1193039dc34ca25f17ecaeb2e6` |
| N-CMAPSS_DS05.h5 | 2599166216 | `ef99ead42ac184503035895797c16e9a7e42554a08074aa760d0bba39db42e23` |
| N-CMAPSS_DS06.h5 | 2549159720 | `91ccf478b21dd6337cfa608f20b647ec04228d59cf4ee59be87fad5f08b17b20` |
| N-CMAPSS_DS07.h5 | 2714714776 | `2f88abc61a532d2e30a6e5ff100a511be4921484a6c7071bc8504e300da4d3bd` |

N-CMAPSS_DS01-005.h5 était déjà présent : identique à la version officielle, conservé.

## Contenu

| DS | Mode de panne | Unités dev | Unités test | Cycles dev | Cycles test | RUL max dev | RUL max test |
|---|---|---|---|---|---|---|---|
| DS01 | HPT | 1, 2, 3, 4, 5, 6 | 7, 8, 9, 10 | 553 | 341 | 99 | 89 |
| DS02 | HPT ou HPT+LPT | 2, 5, 10, 16, 18, 20 | 11, 14, 15 | 446 | 202 | 88 | 75 |
| DS03 | HPT+LPT | 1, 2, 3, 4, 5, 6, 7, 8, 9 | 10, 11, 12, 13, 14, 15 | 663 | 438 | 92 | 92 |
| DS04 | Fan | 1, 2, 3, 4, 5, 6 | 7, 8, 9, 10 | 512 | 344 | 99 | 98 |
| DS05 | HPC | 1, 2, 3, 4, 5, 6 | 7, 8, 9, 10 | 491 | 327 | 99 | 90 |
| DS06 | LPC+HPC | 1, 2, 3, 4, 5, 6 | 7, 8, 9, 10 | 475 | 322 | 98 | 90 |
| DS07 | LPT | 1, 2, 3, 4, 5, 6 | 7, 8, 9, 10 | 468 | 344 | 84 | 95 |
