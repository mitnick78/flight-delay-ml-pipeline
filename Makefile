# Variables
ENV_FILE = .env
DOCKER_DIR = app

# ─────────────────────────────────────
#  Docker
# ─────────────────────────────────────
up:
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) up 

down:
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) down

restart:
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) restart

build:
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) up --build

build_no_cache:
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) build --no-cache
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) up

logs:
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) logs -f

logs-api:
	docker logs -f flight_predictor_api

logs-front:
	docker logs -f flight_predictor_front

logs-db:
	docker logs -f flight_predictor_local_db


# ─────────────────────────────────────
#  ELT
# ─────────────────────────────────────

etl-bronze:
	cd ETL && python3 main_bronze.py

etl-silver:
	cd ETL && python3 main_silver.py

etl-bronze-async:
	cd ETL && python3 main_bronze_async.py

etl-silver-async:
	cd ETL && python3 main_silver_async.py

dbt-staging:
	cd flight_delay_prediction_dbt && dbt run --select tag:staging_init

dbt-gold:
	cd flight_delay_prediction_dbt && dbt run --select tag:gold_init

model-xgboost:
	cd ML_Models && python3 train_xgboost_regressor.py


# ─────────────────────────────────────
# 🧹 Nettoyage
# ─────────────────────────────────────

clean:
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) down -v
	docker network prune -f
	docker container prune -f

run-full:
	bash ./RUN.sh $(ARGS)


# ─────────────────────────────────────
# ℹ️ Aide
# ─────────────────────────────────────

help:
	@echo "╔════════════════════════════════════════════════╗"
	@echo "║             Commandes disponibles              ║"
	@echo "╠════════════════════════════════════════════════╣"
	@echo "║ make up                → Lancer Docker         ║"
	@echo "║ make down              → Arrêter Docker.       ║"
	@echo "║ make build             → Rebuilder             ║"
	@echo "║ make logs              → Voir les logs         ║"
	@echo "║ make etl-bronze        → Lancer ETL            ║"
	@echo "║ make etl-silver        → Lancer ETL            ║"
	@echo "║ make etl-bronze-async  → Lancer ETL async      ║"
	@echo "║ make etl-silver-async  → Lancer ETL async      ║"
	@echo "║ make dbt-staging       → Lancer dbt staging    ║"
	@echo "║ make dbt-gold          → Lancer dbt gold       ║"
	@echo "║ make model-xgboost     → Lancer modèle XGBoost ║"
	@echo "║ make run-full          → Pipeline total.       ║"
	@echo "║ make clean             → Tout nettoyer         ║"
	@echo "╚════════════════════════════════════════════════╝"
