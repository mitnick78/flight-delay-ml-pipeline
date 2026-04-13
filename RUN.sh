#!/usr/bin/env bash

set -Eeuo pipefail
IFS=$'\n\t'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ROOT_DIR/.env"
APP_COMPOSE_FILE="$ROOT_DIR/app/docker-compose.yaml"
DBT_DIR="$ROOT_DIR/flight_delay_prediction_dbt"
LOG_ROOT="$ROOT_DIR/logs/full_runs"
RUN_ID="$(date +"%Y%m%d_%H%M%S")"
RUN_DIR="$LOG_ROOT/$RUN_ID"
MASTER_LOG="$RUN_DIR/run.log"
DRY_RUN=0

mkdir -p "$RUN_DIR"
touch "$MASTER_LOG"

timestamp() {
  date +"%Y-%m-%d %H:%M:%S"
}

log() {
  printf '[%s] %s\n' "$(timestamp)" "$*" | tee -a "$MASTER_LOG"
}

fail() {
  log "ERROR: $*"
  exit 1
}

on_error() {
  local exit_code="$1"
  local line_no="$2"
  local command="$3"
  log "ERROR on line ${line_no}: ${command} (exit code ${exit_code})"
  log "Master log: $MASTER_LOG"
  exit "$exit_code"
}

trap 'on_error "$?" "$LINENO" "$BASH_COMMAND"' ERR

usage() {
  cat <<'EOF'
Usage:
  ./RUN.sh
  ./RUN.sh --dry-run

What it does:
  1. Checks whether the app docker-compose services are already running
  2. If they are, runs `make clean`
  3. Rebuilds and starts the app stack
  4. Waits for PostgreSQL and FastAPI health
  5. Runs ETL/main_bronze_async.py
  6. Runs ETL/main_silver_async.py
  7. Runs dbt staging
  8. Runs dbt gold
  9. Trains the production XGBoost regressor

Logs:
  logs/full_runs/<timestamp>/
EOF
}

while (($# > 0)); do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

resolve_python_bin() {
  if [[ -x "$ROOT_DIR/venv/Scripts/python.exe" ]]; then
    printf '%s\n' "$ROOT_DIR/venv/Scripts/python.exe"
    return
  fi

  if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    printf '%s\n' "$ROOT_DIR/.venv/bin/python"
    return
  fi

  if [[ -x "$ROOT_DIR/venv/bin/python" ]]; then
    printf '%s\n' "$ROOT_DIR/venv/bin/python"
    return
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi

  fail "No usable Python interpreter found."
}

resolve_dbt_bin() {
  if [[ -x "$ROOT_DIR/venv/Scripts/dbt.exe" ]]; then
    printf '%s\n' "$ROOT_DIR/venv/Scripts/dbt.exe"
    return
  fi

  if command -v dbt >/dev/null 2>&1; then
    command -v dbt
    return
  fi

  fail "No usable dbt executable found."
}

run_stage() {
  local stage_name="$1"
  shift

  local stage_log="$RUN_DIR/${stage_name}.log"
  local formatted_command
  : > "$stage_log"
  printf -v formatted_command '%q ' "$@"
  formatted_command="${formatted_command% }"

  log "START ${stage_name}"
  log "Stage log: $stage_log"
  log "Command: $formatted_command"

  if (( DRY_RUN == 1 )); then
    printf '[%s] DRY RUN command: %s\n' "$(timestamp)" "$formatted_command" | tee -a "$stage_log" "$MASTER_LOG"
    log "DONE ${stage_name} (dry run)"
    return
  fi

  "$@" 2>&1 | tee -a "$stage_log" "$MASTER_LOG"
  local exit_code=${PIPESTATUS[0]}
  if (( exit_code != 0 )); then
    fail "Stage '${stage_name}' failed. See $stage_log"
  fi

  log "DONE ${stage_name}"
}

wait_for_postgres() {
  log "Waiting for PostgreSQL to become ready..."

  if (( DRY_RUN == 1 )); then
    log "Skipping PostgreSQL readiness check (dry run)"
    return
  fi

  local attempt
  for attempt in $(seq 1 60); do
    if docker exec flight_predictor_local_db pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
      log "PostgreSQL is ready."
      return
    fi
    sleep 2
  done

  fail "PostgreSQL did not become ready in time."
}

wait_for_api() {
  log "Waiting for FastAPI health endpoint..."

  if (( DRY_RUN == 1 )); then
    log "Skipping FastAPI health check (dry run)"
    return
  fi

  local attempt
  for attempt in $(seq 1 60); do
    if curl -fsS http://127.0.0.1:8000/health/ >/dev/null 2>&1; then
      log "FastAPI is healthy."
      return
    fi
    sleep 2
  done

  fail "FastAPI did not become healthy in time."
}

require_command docker
require_command make
require_command curl

PYTHON_BIN="$(resolve_python_bin)"
DBT_BIN="$(resolve_dbt_bin)"

[[ -f "$ENV_FILE" ]] || fail ".env file not found at $ENV_FILE"
[[ -f "$APP_COMPOSE_FILE" ]] || fail "Compose file not found at $APP_COMPOSE_FILE"
[[ -d "$DBT_DIR" ]] || fail "dbt project directory not found at $DBT_DIR"

if (( DRY_RUN == 0 )); then
  [[ -f "$HOME/.dbt/profiles.yml" ]] || fail "dbt profile not found at $HOME/.dbt/profiles.yml"
fi

set -a
source "$ENV_FILE"
set +a

START_EPOCH="$(date +%s)"

log "Full pipeline run started."
log "Run id: $RUN_ID"
log "Root directory: $ROOT_DIR"
log "Python: $PYTHON_BIN"
log "dbt: $DBT_BIN"
log "Dry run: $DRY_RUN"

RUNNING_SERVICES="$(docker compose -f "$APP_COMPOSE_FILE" --env-file "$ENV_FILE" ps --status running --services || true)"
if [[ -n "$RUNNING_SERVICES" ]]; then
  log "Detected running app services:"
  printf '%s\n' "$RUNNING_SERVICES" | tee -a "$MASTER_LOG"
  run_stage "docker_clean" make -C "$ROOT_DIR" clean
else
  log "No running app services detected. Skipping make clean."
fi

run_stage "docker_build" make -C "$ROOT_DIR" build
wait_for_postgres
wait_for_api

run_stage "etl_bronze_async" bash -lc "cd '$ROOT_DIR/ETL' && '$PYTHON_BIN' main_bronze_async.py"
run_stage "etl_silver_async" bash -lc "cd '$ROOT_DIR/ETL' && '$PYTHON_BIN' main_silver_async.py"
run_stage "dbt_staging" bash -lc "cd '$DBT_DIR' && '$DBT_BIN' run --select tag:staging_init"
run_stage "dbt_gold" bash -lc "cd '$DBT_DIR' && '$DBT_BIN' run --select tag:gold_init"
run_stage "train_xgboost" bash -lc "cd '$ROOT_DIR' && '$PYTHON_BIN' -u ML_Models/train_xgboost_regressor.py"

END_EPOCH="$(date +%s)"
DURATION_SECONDS="$((END_EPOCH - START_EPOCH))"

log "Full pipeline run completed successfully in ${DURATION_SECONDS}s."
log "Master log: $MASTER_LOG"
