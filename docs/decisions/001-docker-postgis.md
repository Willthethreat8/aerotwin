# ADR-001 : Infrastructure Docker + PostGIS
Date : 2026-03-10
Statut : acceptée

## Contexte
Le projet devait stocker des trajectoires de vol (géométries) et des séries météo, et rester reproductible sur
une autre machine.

## Options envisagées
- Fichiers CSV / GeoJSON locaux uniquement.
- PostgreSQL + PostGIS installé sur la machine.
- PostGIS et pgAdmin dans Docker Compose, identifiants dans `.env`.

## Décision
PostGIS 15 et pgAdmin dans `docker-compose.yml`, secrets externalisés dans `.env` (non versionné).

## Conséquences
- Environnement reproductible en une commande (`docker compose up`).
- La base sert aux trajectoires et à la météo, qui sortent du périmètre du modèle et du dashboard final
  (ADR-006, ADR-009). Le modèle et le dashboard n'en dépendent pas.

## Sources
- Commit `2528105`.
- Image `postgis/postgis:15-3.3`.
