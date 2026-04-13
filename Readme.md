# Flight delay ml pipeline

## 📚 Sommaire

- [🧰 Installation](#-installation)
- [⚡ Démarrage rapide](#-démarrage-rapide)
- [🛠️ Commandes disponibles (Makefile)](#️-commandes-disponibles-makefile)
  - [Docker](#docker)
  - [ETL](#etl)
  - [DBT](#dbt)
  - [Modèles ML](#modèles-ml)
  - [Pipeline complet](#pipeline-complet)
- [🐘 Infrastructure (PostgreSQL + pgAdmin)](#-infrastructure-postgresql--pgadmin)
  - [Prérequis](#prérequis)
  - [Lancer les services](#lancer-les-services)
  - [Accéder à pgAdmin](#accéder-à-pgadmin)
  - [Enregistrer le serveur PostgreSQL](#enregistrer-le-serveur-postgresql-dans-pgadmin)
- [🔧 DBT — Configuration & Modèles](#-dbt--configuration--modèles)
  - [Configuration profiles.yml](#configuration-profilesyml)
  - [Lancer les modèles](#lancer-les-modèles)
- [📦 Documentation des utilitaires](#-documentation-des-utilitaires)
  - [utils/geoloc.py](#utilsgelocpy)

---

## 🧰 Installation

### 1. Créer un environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# ou
venv\Scripts\activate           # Windows
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

> ⚠️ Pense à toujours activer ton venv avant de lancer les scripts ou les commandes DBT.

---

## ⚡ Démarrage rapide

```bash
# 1. Lancer l'infrastructure Docker
make up

# 2. Lancer le pipeline complet (ETL + DBT)
make run-full
```

> Pour un contrôle étape par étape, consulte la section [Commandes disponibles](#️-commandes-disponibles-makefile).

---

## 🛠️ Commandes disponibles (Makefile)

### Docker

| Commande      | Description              |
|---------------|--------------------------|
| `make up`     | Lancer les conteneurs    |
| `make down`   | Arrêter les conteneurs   |
| `make build`  | Rebuilder les images     |
| `make logs`   | Afficher les logs        |
| `make clean`  | Tout nettoyer            |

### ETL

| Commande                  | Description                    |
|---------------------------|--------------------------------|
| `make etl-bronze`         | Lancer l'ETL Bronze            |
| `make etl-silver`         | Lancer l'ETL Silver            |
| `make etl-bronze-async`   | Lancer l'ETL Bronze (async)    |
| `make etl-silver-async`   | Lancer l'ETL Silver (async)    |

### DBT

| Commande           | Description               |
|--------------------|---------------------------|
| `make dbt-staging` | Lancer les modèles Staging |
| `make dbt-gold`    | Lancer les modèles Gold    |

### Modèles ML

| Commande               | Description              |
|------------------------|--------------------------|
| `make model-xgboost`   | Lancer le modèle XGBoost |

> ou directement :
>
> ```bash
> cd ML_Models
> python3 train_xgboost_regressor.py
> ```

### Pipeline complet

| Commande         | Description                              |
|------------------|------------------------------------------|
| `make run-full`  | Lancer le pipeline complet (ETL + DBT)   |

---

## 🐘 Infrastructure (PostgreSQL + pgAdmin)

### Prérequis

- Docker + Docker Compose installés
- Python 3.12 (si tu lances les scripts d'ingestion en local)

---

### Lancer les services

Depuis le dossier Docker :

```bash
make up
# ou directement :
docker compose up -d
```

Services exposés :

| Service    | URL                    |
|------------|------------------------|
| PostgreSQL | `localhost:5433`       |
| pgAdmin    | http://localhost:8080  |

---

### Accéder à pgAdmin

URL : http://localhost:8080

| Champ    | Valeur            |
|----------|-------------------|
| Email    | `admin@admin.com` |
| Password | `root`            |

---

### Enregistrer le serveur PostgreSQL dans pgAdmin

**Onglet General**

| Champ | Valeur           |
|-------|------------------|
| Name  | `postgres-local` |

**Onglet Connection**

| Champ                | Valeur     |
|----------------------|------------|
| Host name / address  | `db`       |
| Port                 | `5432`     |
| Maintenance database | `postgres` |
| Username             | `user`     |
| Password             | `password` |

> ⚠️ **IMPORTANT** : Dans pgAdmin, l'hôte PostgreSQL est `db` (nom du service Docker), **pas** `localhost`.

---

## 🔧 DBT — Configuration & Modèles

### Configuration profiles.yml

Le fichier `profiles.yml` doit être placé dans le dossier `.dbt` de ton répertoire personnel :

| OS      | Chemin                                              |
|---------|-----------------------------------------------------|
| macOS   | `/Users/<votre_utilisateur>/.dbt/profiles.yml`      |
| Linux   | `/home/<votre_utilisateur>/.dbt/profiles.yml`       |
| Windows | `C:\Users\<VotreUtilisateur>\.dbt\profiles.yml`     |

Contenu du fichier `profiles.yml` :

```yaml
flight_delay_prediction_dbt:
  outputs:
    dev:
      type: postgres
      host:    "{{ env_var('DB_HOST',     'localhost') }}"
      port:    "{{ env_var('DB_PORT',     '5433') | int }}"
      dbname:  "{{ env_var('DB_NAME',     'flight_predictor') }}"
      schema:  "{{ env_var('DB_SCHEMA',   'public') }}"
      user:    "{{ env_var('DB_USER',     'user') }}"
      pass:    "{{ env_var('DB_PASSWORD', 'password') }}"
      threads: 4
  target: dev
```

> ℹ️ Les valeurs entre simples quotes sont des **valeurs de secours (fallback)**. Elles sont utilisées automatiquement si la variable d'environnement correspondante n'est pas définie. Ces valeurs correspondent à la configuration Docker du projet.
>
> | Variable      | Valeur fallback    |
> |---------------|--------------------|
> | `DB_HOST`     | `localhost`        |
> | `DB_PORT`     | `5433`             |
> | `DB_NAME`     | `flight_predictor` |
> | `DB_SCHEMA`   | `public`           |
> | `DB_USER`     | `user`             |
> | `DB_PASSWORD` | `password`         |

> ⚠️ Ce fichier est en dehors du projet (`~/.dbt/`), il ne sera donc jamais versionné.

---

### Lancer les modèles

Les modèles doivent être lancés **dans cet ordre** :

**Étape 1 — Staging** *(doit être terminé avant de lancer le Gold)*

```bash
make dbt-staging
# ou directement :
cd flight_delay_prediction_dbt
dbt run --select tag:staging_init
```

**Étape 2 — Gold** *(uniquement si le Staging a réussi)*

```bash
make dbt-gold
# ou directement :
cd flight_delay_prediction_dbt
dbt run --select tag:gold_init
```
---
