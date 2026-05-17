#!/usr/bin/env bash
# Wipe + reseed the Railway Postgres database for the linked project/env.
#
# DESTRUCTIVE: drops the public schema (every row in every table) then
# re-runs alembic upgrade head and the Master Export firm import.
# Acceptable pre-launch; do NOT run after 1 June 2026 without a pg_dump.
#
# Usage:
#   scripts/wipe-and-reseed-railway-db.sh                  # interactive
#   scripts/wipe-and-reseed-railway-db.sh --yes            # skip prompt
#   scripts/wipe-and-reseed-railway-db.sh --dry-run        # show plan only
#   scripts/wipe-and-reseed-railway-db.sh --service Postgres
#
# Operates on the currently linked Railway project + environment.
# Verify with `railway status` before running.

set -euo pipefail

PG_SERVICE=""   # auto-detected from project services if empty
ASSUME_YES=0
DRY_RUN=0

usage() {
  sed -n '2,18p' "$0"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service) PG_SERVICE="$2"; shift 2 ;;
    --yes|-y)  ASSUME_YES=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

# ── Tooling ────────────────────────────────────────────────────────────────
for cmd in railway psql jq uv; do
  command -v "$cmd" >/dev/null \
    || { echo "Missing required command: $cmd" >&2; exit 1; }
done

# ── Railway context ────────────────────────────────────────────────────────
railway status --json >/dev/null 2>&1 \
  || { echo "Not linked to a Railway project. Run 'railway link' first." >&2; exit 1; }

CTX=$(railway status --json)
PROJECT=$(jq -r '.name // "unknown"' <<<"$CTX")

# All service names in the project
ALL_SERVICES=$(jq -r '[.environments.edges[].node.serviceInstances.edges[].node.serviceName] | unique | .[]' <<<"$CTX")

# Auto-detect the Postgres service (any name starting with "postgres", case-insensitive)
if [[ -z "$PG_SERVICE" ]]; then
  PG_SERVICE=$(printf '%s\n' "$ALL_SERVICES" | grep -i '^postgres' | head -1 || true)
fi
if [[ -z "$PG_SERVICE" ]]; then
  echo "Could not auto-detect a Postgres service. Available services:" >&2
  printf '  %s\n' $ALL_SERVICES >&2
  echo "Pass --service NAME to pick one." >&2
  exit 1
fi

# Environment name lives on every service's variables — pull from the Postgres one
ENV_NAME=$(
  railway variable list --service "$PG_SERVICE" --json 2>/dev/null \
    | jq -r '.RAILWAY_ENVIRONMENT_NAME // "unknown"'
)

echo "=== Railway context ==="
echo "Project:     $PROJECT"
echo "Environment: $ENV_NAME"
echo "PG service:  $PG_SERVICE"

# ── Pull DATABASE_PUBLIC_URL from the Postgres service ─────────────────────
DATABASE_PUBLIC_URL=$(
  railway variable list --service "$PG_SERVICE" --json 2>/dev/null \
    | jq -r '.DATABASE_PUBLIC_URL // empty'
)
if [[ -z "$DATABASE_PUBLIC_URL" ]]; then
  echo "DATABASE_PUBLIC_URL not set on service '$PG_SERVICE'." >&2
  echo "Enable public networking on the Postgres service in the Railway dashboard." >&2
  exit 1
fi

# Surface host only — never echo the password
PG_HOST=$(printf '%s' "$DATABASE_PUBLIC_URL" | sed -E 's|.*@([^/]+)/.*|\1|')
echo "PG host:     $PG_HOST"
echo

# ── Dry-run short-circuit ──────────────────────────────────────────────────
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[dry-run] would DROP SCHEMA public, alembic upgrade head, re-seed Master Export"
  exit 0
fi

# ── Confirmation ───────────────────────────────────────────────────────────
echo "About to DROP SCHEMA public on the above database."
echo "  - all chat sessions, appointments, reviews, firm users will be erased"
echo "  - then alembic upgrade head + import_master_export.py re-seeds firms"
echo

if [[ "$ASSUME_YES" -ne 1 ]]; then
  read -r -p "Type 'WIPE' to proceed: " CONFIRM
  [[ "$CONFIRM" == "WIPE" ]] || { echo "Aborted."; exit 1; }
fi

export DATABASE_URL="$DATABASE_PUBLIC_URL"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ── Run ────────────────────────────────────────────────────────────────────
echo
echo "=== 1. Dropping public schema ==="
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo
echo "=== 2. Running alembic migrations ==="
( cd "$REPO_ROOT/backend" && uv run alembic upgrade head )

echo
echo "=== 3. Importing Master Export firm data ==="
( cd "$REPO_ROOT/backend" && uv run python scripts/import_master_export.py \
    --input-dir scripts/seed_data/master_export --no-geocode )

echo
echo "=== 4. Verifying row counts ==="
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -P pager=off <<'SQL'
SELECT
  (SELECT count(*) FROM organisations)         AS organisations,
  (SELECT count(*) FROM offices)               AS offices,
  (SELECT count(*) FROM price_cards)           AS price_cards,
  (SELECT count(*) FROM complaints_summary)    AS complaints_summary,
  (SELECT count(*) FROM regulatory_summary)    AS regulatory_summary;
SQL

echo
echo "Done. Smoke-test with:"
echo "  curl https://backend-production-2962.up.railway.app/health"
