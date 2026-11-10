# AeroTwin — Roadmap

**Projet terminé (novembre 2026).** Ce document est conservé comme trace de la feuille de route initiale : le reste du texte n'a pas été mis à jour, seules les lignes « Statut » ont été ajoutées. Les raisons de la clôture sont dans [ADR-006](docs/decisions/006-cloture-projet.md) : périmètre trop large pour un projet solo, sujet ramené à son cœur, réorientation du portfolio.

| Phase | Statut |
|---|---|
| 0-1 : base du projet, EDA FD001, trajectoires, météo | Réalisée |
| 2 : exploration N-CMAPSS | Réalisée |
| 3 : ETL `src/` | Réalisée, sans Prefect ni dbt, abandonnés ([ADR-006](docs/decisions/006-cloture-projet.md)) |
| 4 : machine learning et MLflow | 4.1 et 4.2 réalisées, puis modèle par fichier ; LSTM / Transformer et détection d'anomalies abandonnés ([ADR-006](docs/decisions/006-cloture-projet.md)) |
| 5 : CI/CD | Réduite à une CI Pytest ([ADR-006](docs/decisions/006-cloture-projet.md)) |
| 6 : dashboard | Réduite à trois pages sans météo ni carte des trajectoires ([ADR-006](docs/decisions/006-cloture-projet.md)) |
| 7 : streaming temps réel | Abandonnée ([ADR-006](docs/decisions/006-cloture-projet.md)) |
| 8 : API FastAPI et déploiement cloud | Abandonnée ([ADR-006](docs/decisions/006-cloture-projet.md)) |
| 9 : IA générative et agents | Abandonnée ([ADR-006](docs/decisions/006-cloture-projet.md)) |

## État actuel

### Fait (Phases 0 & 1) ✅

| Composant | État |
|---|---|
| Infrastructure Docker PostGIS + pgAdmin | ✅ |
| Dataset NASA FD001 — EDA, RUL calculé, rolling features | ✅ |
| Suppression capteurs constants (7 colonnes) | ✅ |
| Trajectoires GPS simulées depuis LFBO (5 moteurs) | ✅ |
| Collecte météo historique — Open-Meteo ERA5 (1 an) | ✅ |
| Collecte météo live — Aviation Weather Center (Phase 7) | ✅ |
| Ingestion PostGIS — trajectoires + météo | ✅ |
| Tests Pytest | ✅ |
| Secrets externalisés (.env / .env.example) | ✅ |
| requirements.txt figé | ✅ |

### Architecture météo
- **Open-Meteo (ERA5)** → historique long terme → corrélation ML
- **Aviation Weather Center** → METAR live → dashboard temps réel (Phase 7)
- La météo surface n'alimente **pas** le modèle ML — les inputs du modèle sont les conditions de vol (`alt`, `Mach`, `TRA`, `T2`) + la classe de vol `Fc`, issues de N-CMAPSS

---

## Pivot dataset : FD001 → N-CMAPSS

FD001 (C-MAPSS) est un dataset synthétique sans timestamps ni coordonnées réelles.
N-CMAPSS (NASA 2021, format HDF5) est piloté par de **vrais profils de vol commerciaux**
(altitude, Mach, manette des gaz enregistrés en vol), avec phases montée / croisière /
descente et une dégradation physiquement cohérente en deux régimes (sain puis anormal).
C'est ce dataset qui rend le projet physiquement honnête.

| | **C-MAPSS FD001** (phases 0-1) | **N-CMAPSS DS01-005** (à partir de la phase 2) |
|---|---|---|
| Format | texte `.txt`, 1 ligne/cycle | HDF5, groupes `W / X_s / X_v / T / A / Y`, 1 Hz |
| Nature | 100 % simulé (modèle thermo) | model-based **piloté par des enregistrements de vol réels** |
| Volume | ~20 k lignes (déjà agrégées) | ~4,9 M lignes `dev` + ~2,7 M `test` (~2,8 Go) → **agrégation obligatoire** |
| Moteurs | 100 train / 100 test | 10 unités : 6 `dev` (`unit` 1→6) + 4 `test` (`unit` 7→10) |
| Conditions de vol | 3 `op_settings` abstraits ; **1 régime** (FD001), 6 régimes (FD002/004) | 4 signaux **continus** : `alt`, `Mach`, `TRA`, `T2` (varient dans chaque vol) |
| Type de vol | non modélisé | `Fc` = **3 classes** selon la durée (1 : <3 h, 2 : 3-5 h, 3 : >5 h) |
| Capteurs | 21 capteurs anonymes | 14 physiques (`X_s`) + 14 virtuels (`X_v`) + 10 paramètres de santé (`T`, θ) |
| RUL | **à calculer** (`max_cycle − cycle`) | **fournie** (groupe `Y`) |
| Panne | HPC (FD001/002), + Fan (FD003/004) | DS01 : dégradation efficacité HPT ; `hs` = 1 (sain) → 0 (anormal) |

> ⚠️ Le « 5 ou 6 conditions de vol » est un concept **C-MAPSS** (FD002/FD004 = 6 régimes
> discrets par clustering des `op_settings`). N-CMAPSS ne fonctionne pas ainsi : conditions
> **continues** (`W`) + 3 classes de vol (`Fc`). Rien à clusteriser.

---

## Extension multi-DS (DS02 → DS08)

N-CMAPSS est une **famille de ~9 fichiers HDF5 indépendants**, pas un dataset découpé.
Même schéma (`W / X_s / X_v / T / A / Y`, splits `dev` / `test`) → le code d'extraction
est le même pour tous. Le `-005` de `DS01-005.h5` est un numéro de version de fichier,
pas « 5 sur 8 ».

### Ce qui change d'un DS à l'autre

| DS | Mode(s) de dégradation | Intérêt pour le projet |
|---|---|---|
| **DS01** *(en place)* | efficacité HPT — 1 seul mode | signal propre → **baseline** (phases 3-4), boucle de dev rapide |
| **DS02** | HPT + LPT, dérivé d'une vraie flotte | **référence de la littérature** — indispensable pour un RMSE comparable |
| DS03 | HPT + LPT, conditions plus bruitées | robustesse au bruit |
| DS04 → DS07 | Fan / HPC / LPC / LPT (un composant chacun) | variété des modes de panne |
| DS08a / DS08c / DS08d | tous composants, multi-modes | cas le plus difficile |

*(Répartition exacte modes / nb d'unités : à confirmer sur le NASA Prognostics Data Repository — PCoE.)*

### Où chaque DS apporte quelque chose

| Phase | Multi-DS utile ? | Pourquoi |
|---|---|---|
| 3 — ETL | oui, par design | l'ETL doit tourner **par DS** et taguer la provenance (`ds_id`, `fault_mode`) |
| 4 — ML | **oui** | DS01 = 10 unités seulement → CV fragile. **DS02** pour le benchmark ; DS03-08 pour un axe « généralisation multi-mode » ou anomaly detection (4.4) assumé |
| 5 — CI/CD | non | tourne sur des fixtures, jamais sur les `.h5` |
| 6 — Dashboard | oui, présentation | pooler les unités `dev` de plusieurs DS → flotte de ~30-40 moteurs crédible |
| 7 — Streaming | non | données = ADS-B live, découplé de C-MAPSS |
| 8 — API | non | `/predict` prend les conditions de vol en entrée ; seule la qualité du modèle compte |
| 9 — RAG / agents | marginal | rapports d'anomalie variés (« moteur 23 : perte efficacité LPC ») plus riches |

### Règle anti-pool (Phase 4)

Ne **jamais** concaténer les DS aveuglément : chaque DS a des modes de panne différents,
DS03+ changent les conditions opératoires → **domain shift**. Trois approches propres :

1. entraîner + évaluer **par DS**, puis tableau comparatif ;
2. union avec `fault_mode` en **feature catégorielle**, évaluation **par DS** ;
3. **leave-one-DS-out** pour revendiquer de la généralisation.

### Impact ETL / infra (à faire quand la Phase 4 en aura besoin — hors périmètre Phase 3)

- Rendre l'ETL **DS-agnostique** : `read_ncmapss(ds_id="DS02")` résolvant le fichier par
  motif (`data/raw/ncmapss/N-CMAPSS_DS02*.h5`), chaque ligne taguée `ds_id` + `fault_mode`.
  *Aujourd'hui `read_ncmapss` ne lit que DS01 (chemin en dur).*
- Pooler ou non est une **décision de la Phase 4**, pas le rôle de l'ETL.
- Rappel ML : seuls `A`, `W`, `X_s`, `Y` alimentent le modèle. `X_v` (capteurs virtuels)
  et `T` (paramètres de santé θ) sont **exclus — data leakage**.
- Coût réel = **25-30 Go** à télécharger + temps de traitement. Après agrégation au cycle,
  même les 9 DS tiennent en quelques dizaines de milliers de lignes → aucun souci Postgres.

---

## Roadmap

### Phase 2 — Exploration N-CMAPSS

**Statut : Réalisée.**

**Objectif : comprendre le HDF5 avant de coder quoi que ce soit**

- Télécharger `N-CMAPSS_DS01-005.h5` depuis NASA Prognostics Repository
- Notebook `05_exploration_ncmapss.ipynb`
  - Lire les groupes HDF5 : `W` (conditions vol : `alt`, `Mach`, `TRA`, `T2`), `X_s` (14 capteurs physiques), `X_v` (14 capteurs virtuels), `T` (10 paramètres de santé θ), `A` (auxiliaire : `unit`, `cycle`, `Fc`, `hs`), `Y` (RUL)
  - EDA : distributions, dérive capteurs avant panne, capteurs constants à supprimer
  - Comprendre la structure `unit` / `cycle` / `Fc` (classe de vol) / `hs` (health state 1→0)
  - Rolling features sur les capteurs pertinents
- Reset base Docker (schéma FD001 obsolète)

---

### Phase 3 — ETL `src/`

**Statut : Réalisée. Prefect et dbt abandonnés, voir [ADR-006](docs/decisions/006-cloture-projet.md).**

**Objectif : sortir des notebooks, code réutilisable et propre**

```
src/
├── config.py      # charge .env — agnostique local/cloud (DB_URL)
├── extract.py     # lit HDF5 par chunks (h5py) — jamais tout en mémoire
├── transform.py   # agrégation 1 Hz→cycle, rolling stats, aplatit la structure HDF5 (RUL fournie par `Y`)
└── load.py        # insère dans PostGIS par batch
```

- ETL agnostique de la destination : changer `DB_URL` dans `.env` suffit pour basculer local → cloud
- Orchestration avec Prefect (`pipeline.py`)
- Transformations SQL versionnées avec dbt (`staging/`, `marts/`)
- Déplacer les credentials du notebook 04 vers `config.py`

**Décision d'architecture : agrégation au niveau cycle, le plus tôt possible.**
DS01 = millions de lignes à 1 Hz. Résumé par (unit, cycle), on retombe sur quelques
milliers de lignes : EDA, rolling features, XGBoost et PostGIS restent légers.
Le 1 Hz brut ne sort jamais de `extract → aggregate`.

**Clause de repli (sécurise le deadline).** Checkpoint mi-août : si `read_ncmapss` +
`aggregate_to_cycles` ne tournent pas avec leurs tests verts, retour à C-MAPSS FD001-004
(données dans le repo, code legacy dans l'historique git).

---

### Phase 4 — Machine Learning + MLflow

**Statut : 4.1 et 4.2 réalisées. LSTM / Transformer et détection d'anomalies abandonnés, voir [ADR-006](docs/decisions/006-cloture-projet.md).**

**Objectif : modèle de prédiction RUL traçable et reproductible**

**4.1 Baseline XGBoost**
- Features conditions de vol N-CMAPSS : les **4** variables du groupe `W` — `alt`, `Mach`, `TRA` (angle manette des gaz), `T2` — agrégées par cycle (`mean` / `std` / `min` / `max`), + `Fc` (classe de vol, catégorielle)
  - ⚠️ `TRA` (réglage de puissance pilote) est essentiel pour normaliser les capteurs selon le régime — ne pas l'oublier
  - ⚠️ la colonne s'appelle `alt` dans le HDF5, **pas** `altitude`
- + rolling stats capteurs (`X_s`)
- RUL cappé à 125 (à comparer avec non cappé)
- Split stratifié par `unit` — pas de data leakage entre moteurs
- Métriques : RMSE, MAE, R²
- Objectif : battre RMSE 36.89 (référence Sara-Esm/Predictive-Maintenance, split aléatoire non stratifié)
- **Datasets** : baseline sur DS01, puis DS02 pour le résultat comparable à la littérature.
  Pooling multi-DS uniquement selon la « règle anti-pool » (cf. *Extension multi-DS*).

**4.2 MLflow**
- Logger chaque run : hyperparamètres, métriques, modèle
- Comparer avec/sans RUL cap, avec/sans rolling features
- Sauvegarder le meilleur modèle en artefact

**4.3 LSTM / Transformer (upgrade)**
- Architecture séquentielle adaptée aux phases de vol (montée → croisière → descente)
- XGBoost reste la baseline de référence

**4.4 Anomaly Detection (module parallèle)**
- Isolation Forest ou Autoencoder sur les capteurs
- Détecter les comportements anormaux indépendamment du RUL
- Double la valeur métier : "moteur va tomber en panne dans X cycles" + "comportement anormal détecté maintenant"

---

### Phase 5 — CI/CD GitHub Actions

**Statut : Réduite à une CI Pytest (`.github/workflows/tests.yml`), voir [ADR-006](docs/decisions/006-cloture-projet.md).**

```yaml
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

---

### Phase 6 — Dashboard Streamlit

**Statut : Réduite à trois pages, sans météo ni carte des trajectoires, voir [ADR-006](docs/decisions/006-cloture-projet.md).**

**Vue Flotte**
- Tableau moteurs : RUL prédit, statut (OK / Attention / Critique)
- Alertes Anomaly Detection en temps réel
- Carte folium multi-aéroports (LFBO, CDG, LHR, FRA) — usage visualisation uniquement

**Vue Moteur**
- Évolution capteurs clés au fil des cycles
- RUL prédit vs RUL réel
- Phases de vol (montée / croisière / descente)

**Vue Météo**
- Conditions METAR live LFBO (Aviation Weather Center) — contexte opérationnel sol
- Pas d'alimentation du modèle ML

---

### Phase 7 — Pipeline Streaming Temps Réel (ADS-B → Kafka → Spark → Lakehouse)

**Statut : Abandonnée, voir [ADR-006](docs/decisions/006-cloture-projet.md).**

**Objectif : passer du batch au temps réel sur données live — la compétence la plus demandée en 2026**

**7.1 Ingestion ADS-B live**
- OpenSky Network API : positions ADS-B réelles des avions dans un rayon autour de LFBO
- Producer Python : polling API (~10s) → publication dans un topic **Kafka** (`adsb.raw`)
- Kafka via docker-compose (mode KRaft, sans ZooKeeper) — s'ajoute au PostGIS existant

**7.2 Traitement Spark Structured Streaming**
- Job PySpark consommant `adsb.raw` : parsing, filtrage qualité, enrichissement (phase de vol estimée via altitude/vitesse verticale, distance à LFBO)
- Agrégations fenêtrées (tumbling window 1 min) : trafic par zone, altitudes moyennes
- Jointure avec le RUL prédit (Phase 4) pour scorer la santé des moteurs simulés associés aux vols

**7.3 Couche lakehouse Apache Iceberg**
- Données brutes + enrichies écrites en tables **Iceberg** (PyIceberg, catalogue SQLite local)
- Requêtage analytique avec **DuckDB** (extension Iceberg) — time travel, schema evolution démontrés
- PostGIS conserve les agrégats servant le dashboard et l'API (serving layer)
- Architecture type **médaillon** : bronze (ADS-B brut) → silver (enrichi) → gold (agrégats PostGIS)

**7.4 Visualisation temps réel**
- Dashboard Streamlit (Phase 6) : carte folium auto-rafraîchie avec les vols live autour de LFBO
- Tracé couleur selon santé moteur (vert / orange / rouge)
- Alertes Anomaly Detection recalculées au fil du stream

> **Ce que cette phase remplace** : l'ancien générateur de profils synthétiques. On passe
> de données simulées à un vrai flux événementiel — batch + streaming coexistent
> dans la même architecture (lambda simplifiée).

---

### Phase 8 — API FastAPI + Déploiement Cloud

**Statut : Abandonnée, voir [ADR-006](docs/decisions/006-cloture-projet.md). Le dashboard est préparé pour Streamlit Community Cloud.**

**FastAPI /predict**
```
POST /predict
{
  "unit": 12,
  "cycle": 87,
  "fc": 3,
  "alt": 35000,
  "mach": 0.84,
  "tra": 65.0,
  "t2": -45.2,
  ...
}
→ { "rul_predicted": 104.2 }
```
- Inputs : les 4 conditions de vol `W` (`alt`, `mach`, `tra`, `t2`) + `fc`, pas météo surface
- Modèle XGBoost chargé depuis artefact MLflow

**Migration base de données**
- Supabase (500 MB) trop petit pour N-CMAPSS traité
- Cible : GCP Cloud SQL (PostGIS natif, crédits 300$)
- Basculement : une ligne dans `.env` — ETL inchangé

**Déploiement**
- GCP Cloud Run pour FastAPI
- Azure Container Apps comme cible moyen terme (écosystème Airbus/Toulouse)

---

### Phase 9 — IA Générative & Agents

**Statut : Abandonnée, voir [ADR-006](docs/decisions/006-cloture-projet.md).**

**Objectif : démontrer une infrastructure de données AI-ready — 2e sujet de recrutement 2026 avec le streaming**

**9.1 Pipeline données AI-ready (prérequis RAG)**
- Vectorisation des données flotte : résumés d'état moteur, rapports d'anomalies, contexte météo → embeddings dans **pgvector** (extension PostgreSQL, cohérente avec PostGIS)
- Pipeline d'indexation orchestré par Prefect (réutilise la Phase 3)

**9.2 Fleet Copilot (RAG)**
- Assistant conversationnel sur l'état de la flotte
- Retrieval hybride : recherche vectorielle (pgvector) + requêtes SQL générées (text-to-SQL sur PostGIS)
- LlamaIndex / LangChain + API LLM
- Évaluation : jeu de questions/réponses de référence, mesure de la fidélité des réponses

**9.3 Agent de Diagnostic**
- Workflow LangGraph : détection anomalie (Phase 4.4) → contexte historique PostGIS → corrélation stream ADS-B/météo (Phase 7) → rapport structuré → alerte
- Déclenchement automatique via Prefect

**9.4 Recommandations décarbonation**
- RUL prédit + profil de vol → ajustements (altitude, vitesse) pour préserver les moteurs
- Pertinent pour OpenAirlines

---

## Ce que ce projet démontre sur le CV

| Compétence | Où |
|---|---|
| ETL / pipeline de données | Phase 3 : src/ + Prefect + dbt |
| Bases de données spatiales | PostGIS + GeoAlchemy2 |
| Machine Learning | Phase 4 : XGBoost + MLflow |
| Séries temporelles | Phase 4+ : LSTM / Transformer |
| Anomaly Detection | Phase 4+ : module parallèle |
| CI/CD | Phase 5 : GitHub Actions |
| Dashboard | Phase 6 : Streamlit |
| Streaming / event-driven | Phase 7 : Kafka + Spark Structured Streaming |
| Lakehouse / open table formats | Phase 7 : Iceberg + DuckDB (médaillon) |
| API REST | Phase 8 : FastAPI /predict |
| Cloud / Déploiement | Phase 8 : GCP Cloud Run |
| IA Générative / RAG / Agents | Phase 9 : Fleet Copilot + pgvector + LangGraph |
| Docker | docker-compose multi-services |
| Tests | Pytest |
| Sujet métier aéro | Maintenance prédictive moteur, LFBO, N-CMAPSS |
