#!/usr/bin/env bash
set -euo pipefail
if docker container inspect myra-backend >/dev/null 2>&1 || \
   docker container inspect myra-db >/dev/null 2>&1 || \
   { command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet myra-watch.service; }; then
  echo 'REFUSED: this Docker host contains production Myra services or its quarantine watcher. Use a separate test host/CI.' >&2
  exit 2
fi
task_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
task_name="myra-repair-test-$(date +%s)-$$"
task_password=$(python3 -c 'import secrets; print(secrets.token_hex(24))')
cleanup() {
  docker rm -f "$task_name-db" >/dev/null 2>&1 || true
  docker network rm "$task_name" >/dev/null 2>&1 || true
  docker image rm "$task_name-backend" >/dev/null 2>&1 || true
}
trap cleanup EXIT
python3 "$task_root/ops/tests/verify_publish_linux.py"
docker build -t "$task_name-backend" "$task_root/backend"
docker network create --internal "$task_name" >/dev/null
docker run -d --name "$task_name-db" --network "$task_name" \
  --tmpfs /var/lib/postgresql/data \
  -e POSTGRES_DB=myra_repair_test -e POSTGRES_USER=myra_test \
  -e POSTGRES_PASSWORD="$task_password" pgvector/pgvector:pg17 >/dev/null
task_ready=false
for task_attempt in $(seq 1 60); do
  if docker exec "$task_name-db" pg_isready -U myra_test -d myra_repair_test >/dev/null 2>&1; then
    task_ready=true
    break
  fi
  sleep 1
done
if [ "$task_ready" != true ]; then
  echo 'Disposable PostgreSQL did not become ready' >&2
  exit 1
fi
docker run --rm --network "$task_name" \
  -e "DATABASE_URL=postgresql+asyncpg://myra_test:$task_password@$task_name-db:5432/myra_repair_test" \
  -e DATABASE_SSL=false -e MYRA_ISOLATED_TEST=1 -e ENVIRONMENT=development \
  -e JWT_SECRET=isolated-integration-test-key-at-least-32-characters \
  -e STT_ENABLED=false -e RECALL_ENABLED=false -e PROFILE_ENABLED=false \
  -e CRISIS_ALERT_ENABLED=false -e RAG_KEEPWARM_INTERVAL_S=0 -e DISABLE_RAG_STARTUP_WARMUP=true \
  --entrypoint python "$task_name-backend" integration/verify_postgres.py
