# Aide-mémoire des Commandes Terminal et Docker

## 1. Navigation et Gestion de Fichiers (Terminal)
* `mkdir [nom]` : (Make Directory) Crée un nouveau dossier.
* `cd [nom]` : (Change Directory) Déplace le terminal à l'intérieur du dossier spécifié.
* `touch [nom_fichier]` : Crée un fichier vide avec son extension (ex: .md, .yml, .py).
* `ls` : (List) Affiche tout le contenu (fichiers et dossiers) du répertoire actuel.

## 2. Gestion de l'Infrastructure (Docker)
* `docker-compose up -d` : Lit le fichier docker-compose.yml, télécharge les images nécessaires et allume les machines virtuelles en arrière-plan (-d pour detached).
* `docker ps` : (Process Status) Liste tous les conteneurs (machines) actuellement allumés et fonctionnels.
* `docker-compose down` : Arrête proprement toutes les machines et les supprime.
* `docker ps` : (Process Status) À lancer SYSTÉMATIQUEMENT après un `docker-compose up -d`. Permet de vérifier que le statut (STATUS) des conteneurs est bien sur "Up" et qu'il n'y a pas eu de crash au démarrage.

## 3. Environnement Python (venv)
* `python3 -m venv venv` : Crée un environnement virtuel (une bulle isolée).
* `source venv/bin/activate` : Active la bulle (le préfixe `(venv)` apparaît).
* `pip install [nom_paquet]` : Installe une bibliothèque Python.
* `python3 -m pip install --upgrade pip` : Met à jour le gestionnaire d'installation lui-même.
* `jupyter notebook` : Lance l'interface web pour coder.

## 4. Gestion de versions (Git & GitHub)
* `git init` : Initialise un suivi Git local dans le dossier du projet.
* `git add .` : Prépare tous les fichiers modifiés (qui ne sont pas dans `.gitignore`) pour la sauvegarde.
* `git commit -m "message"` : Valide la sauvegarde avec un message descriptif court.
* `git push -u origin main` : Envoie le code validé vers le serveur distant GitHub.