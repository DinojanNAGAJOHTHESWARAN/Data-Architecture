# MediDataLab — Architecture de données containerisée pour un projet IA

Pipeline d'ingestion de données médicales combinant PostgreSQL (données structurées) et MongoDB (données semi-structurées), entièrement orchestré avec Docker Compose.

## Sommaire

- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Structure du projet](#structure-du-projet)
- [Installation](#installation)
- [Démarrage](#démarrage)
- [Accès aux interfaces](#accès-aux-interfaces)
- [Utilisation de pgAdmin](#utilisation-de-pgadmin)
- [Utilisation de Mongo Express](#utilisation-de-mongo-express)
- [Supervision avec Portainer](#supervision-avec-portainer)
- [Surveillance des ressources](#surveillance-des-ressources)
- [Relancer une ingestion](#relancer-une-ingestion)
- [Idempotence](#idempotence)
- [Dépannage](#dépannage)
- [Arrêt de l'environnement](#arrêt-de-lenvironnement)

## Architecture

```
                         Docker Host (medical_net)
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│   PostgreSQL :5432 ──── pgAdmin :5050                        │
│        ▲                                                     │
│        │                                                     │
│   MongoDB :27017 ──── Mongo Express :8081                    │
│        ▲                                                     │
│        │                                                     │
│   data_ingestor (Python) ◄──── lit CSV / JSON                │
│        │                                                     │
│   Portainer :9000 (supervision de tous les services)         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

- **PostgreSQL** : médecins, patients, médicaments, prescriptions (données structurées, relations via clés étrangères)
- **MongoDB** : consultations — symptômes, diagnostics (données semi-structurées, schéma flexible)
- **data_ingestor** : script Python qui lit les fichiers `data_small/`, `data_medium/`, `data_large/` et alimente les deux bases

## Prérequis

- Docker et Docker Compose installés
- Les dossiers `data_small/`, `data_medium/`, `data_large/` placés à la racine du projet, chacun contenant :
  - `doctors.csv`
  - `patients.csv`
  - `medications.csv`
  - `prescriptions.csv`
  - `consultations.json`

## Structure du projet

```
projet/
├── .env                  # secrets réels (jamais commité)
├── .env.example          # modèle de secrets (valeurs fictives)
├── .gitignore
├── docker-compose.yaml
├── data_small/
├── data_medium/
├── data_large/
└── app/
    ├── Dockerfile
    ├── requirements.txt
    ├── config.py
    ├── database.py
    ├── ingest_postgres.py
    ├── ingest_mongo.py
    └── main.py
```

## Installation

1. Cloner ou récupérer le projet
2. Créer le fichier `.env` à partir du modèle :
   ```bash
   cp .env.example .env
   ```
3. Renseigner des valeurs réelles dans `.env` :
   ```env
   POSTGRES_USER=dino
   POSTGRES_PASSWORD=kami
   POSTGRES_DB=medical_db
   POSTGRES_HOST=postgres
   POSTGRES_PORT=5432

   MONGO_USER=dino
   MONGO_PASSWORD=kami
   MONGO_URI=mongodb://dino:kami@mongo:27017/

   PGADMIN_EMAIL=admin@example.com
   PGADMIN_PASSWORD=changeme

   MONGO_EXPRESS_USER=changeme
   MONGO_EXPRESS_PASSWORD=changeme
   ```
4. Vérifier que `data_small/`, `data_medium/`, `data_large/` sont bien à la racine, au même niveau que `docker-compose.yaml`

> ⚠️ Le fichier `.env` ne doit jamais être commité sur GitHub — il est exclu via `.gitignore`.

## Démarrage

Construire les images et démarrer l'ensemble des services :

```bash
docker compose up --build -d
```

Suivre les logs du pipeline d'ingestion en temps réel :

```bash
docker compose logs -f app
```

Un démarrage réussi affiche dans l'ordre :
```
🔥 PIPELINE STARTED
📦 Processing dataset: /data_small
📦 Processing dataset: /data_medium
📦 Processing dataset: /data_large
🎯 ALL DATASETS COMPLETED SUCCESSFULLY
```

## Accès aux interfaces

| Service | URL | Identifiants |
|---|---|---|
| pgAdmin | http://localhost:5050 | `PGADMIN_EMAIL` / `PGADMIN_PASSWORD` (`.env`) |
| Mongo Express | http://localhost:8081 | `MONGO_EXPRESS_USER` / `MONGO_EXPRESS_PASSWORD` (`.env`) |
| Portainer | http://localhost:9000 | Compte admin créé au premier lancement (< 5 min après démarrage du conteneur) |

## Utilisation de pgAdmin

1. Ouvrir http://localhost:5050 et se connecter avec les identifiants pgAdmin
2. Clic droit sur **Servers** → **Register > Server**
   - **Onglet Général** → Nom : `medical_db` (libre)
   - **Onglet Connexion** :
     - Nom d'hôte : `postgres` (nom du service Docker, **pas** `localhost`)
     - Port : `5432`
     - Base de données de maintenance : valeur de `POSTGRES_DB`
     - Identifiant : valeur de `POSTGRES_USER`
     - Mot de passe : valeur de `POSTGRES_PASSWORD`
3. Parcourir `Servers > medical_db > Databases > medical_db > Schemas > public > Tables` pour voir `doctors`, `patients`, `medications`, `prescriptions`
4. Vérifier les données via le Query Tool :
   ```sql
   SELECT * FROM patients LIMIT 10;
   ```

> Ne pas confondre les identifiants du compte pgAdmin (email de connexion à l'interface) avec ceux du compte PostgreSQL (`POSTGRES_USER` / `POSTGRES_PASSWORD`) — ce sont deux paires distinctes.

## Utilisation de Mongo Express

1. Ouvrir http://localhost:8081 et s'authentifier avec les identifiants Mongo Express
2. Sélectionner la base **medical**, puis la collection **consultations**
3. Vérifier la présence des documents et leur structure :
   ```json
   {
     "consultation_id": "CONS0001",
     "patient_id": "P0042",
     "date": "2024-03-15",
     "symptoms": "Fièvre persistante, toux sèche...",
     "diagnosis": "Infection respiratoire haute..."
   }
   ```

## Supervision avec Portainer

1. Ouvrir http://localhost:9000 et créer le compte administrateur au premier accès
2. Sélectionner l'environnement **local**
3. **Dashboard** : vue d'ensemble (conteneurs running/stopped, volumes, réseaux)
4. **Containers** : statut de chaque service — vérifier que `postgres_db` et `mongo_db` affichent **healthy**
5. Cliquer sur un conteneur pour consulter ses **Logs** en temps réel ou ses **Stats** (CPU/RAM/réseau/I/O)
6. **Volumes** et **Networks** dans le menu de gauche : gestion sans ligne de commande

## Surveillance des ressources

Pendant une ingestion, observer la consommation CPU/RAM en temps réel :

```bash
docker stats postgres_db mongo_db data_ingestor
```

## Relancer une ingestion

```bash
docker compose restart app
docker compose logs -f app
```

Pour tester différentes volumétries (60 000 / 600 000 / 6 000 000 lignes selon les jeux de données fournis), observer dans `docker stats` :
- l'évolution du CPU et de la mémoire
- le temps total affiché en fin de chaque dataset (`⏱️ ... completed in Xs`)

## Idempotence

Le pipeline est conçu pour être ré-exécutable sans créer de doublons :

- **PostgreSQL** : chaque insertion utilise `ON CONFLICT (id) DO NOTHING`
- **MongoDB** : un index unique sur `consultation_id` empêche les doublons

> ⚠️ Si l'index unique MongoDB a été ajouté après une ou plusieurs ingestions sans contrôle, la collection peut déjà contenir des doublons antérieurs. Dans ce cas, vider la collection avant de relancer :
> ```bash
> docker exec -it mongo_db mongosh -u <MONGO_USER> -p <MONGO_PASSWORD> --authenticationDatabase admin --eval "use medical; db.consultations.drop();"
> ```

## Dépannage

| Symptôme | Cause / solution |
|---|---|
| `FileNotFoundError` sur un CSV | Vérifier que `DATASETS` dans `config.py` correspond aux chemins montés (`/data_small`, etc.) |
| Portainer affiche une page vide | Créer le compte admin dans les 5 minutes suivant le démarrage du conteneur, sinon le redémarrer (`docker compose restart portainer`) |
| Erreur de connexion PostgreSQL au démarrage | Vérifier le `healthcheck` et `depends_on: condition: service_healthy` |
| `DuplicateKeyError` lors de la création de l'index Mongo | La collection contient déjà des doublons antérieurs — la vider avant de relancer (voir section Idempotence) |
| Champ "Identifiant" pgAdmin pré-rempli avec un email | Remplacer par la valeur de `POSTGRES_USER`, pas le compte pgAdmin |

## Arrêt de l'environnement

Arrêter les services (les données restent persistées grâce aux volumes) :

```bash
docker compose down
```

Pour repartir complètement de zéro (supprime aussi les volumes, donc toutes les données) :

```bash
docker compose down -v
```
