#!/bin/bash
# app.sh — run Evalify on the cluster login node: MongoDB (user space) + backend + frontend.
#
#   bash infra/cluster/app.sh start     # database (if needed), backend :47823, frontend :5173
#   bash infra/cluster/app.sh stop      # backend + frontend (the database keeps running; mongo.sh stop for that)
#   bash infra/cluster/app.sh status
#
# The backend uses the persistent database from infra/cluster/mongo.sh (credentials in
# /scratch/$USER/evalify/run/mongo.env) and the GPU models of the running Slurm job (endpoints file).
# Open the app through VS Code port forwarding: 5173 (UI) and 47823 (API docs at /docs).
set -euo pipefail

REPO=$(cd "$(dirname "$0")/../.." && pwd)
BASE=/scratch/$USER/evalify
RUN=$BASE/run
LOGS=$BASE/logs
PY=/scratch/$USER/evalify/envs/backend/bin/python
mkdir -p "$RUN" "$LOGS"

# Is the process in a pid file alive?
alive() { [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null; }

case "${1:-status}" in
  start)
    bash "$REPO/infra/cluster/mongo.sh" start
    [ -f "$RUN/mongo.env" ] || { echo "run infra/cluster/mongo.sh init first"; exit 1; }
    # Backend on the persistent database, v2 pipeline
    if alive "$RUN/backend.pid"; then echo "backend already running"; else
      (cd "$REPO/backend" && set -a && . "$RUN/mongo.env" && set +a && EVALIFY_PIPELINE=v2 \
        nohup "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 47823 >> "$LOGS/backend.log" 2>&1 & echo $! > "$RUN/backend.pid")
      echo "backend starting on :47823 (log $LOGS/backend.log)"
    fi
    # Frontend dev server (proxies /api to the backend)
    if alive "$RUN/frontend.pid"; then echo "frontend already running"; else
      (cd "$REPO/frontend" && nohup npm run dev -- --host 127.0.0.1 --port 5173 >> "$LOGS/frontend.log" 2>&1 & echo $! > "$RUN/frontend.pid")
      echo "frontend starting on :5173 (log $LOGS/frontend.log)"
    fi
    ;;
  stop)
    for p in backend frontend; do
      if alive "$RUN/$p.pid"; then pkill -P "$(cat "$RUN/$p.pid")" 2>/dev/null || true; kill "$(cat "$RUN/$p.pid")"; echo "$p stopped"; fi
      rm -f "$RUN/$p.pid"
    done
    ;;
  status)
    bash "$REPO/infra/cluster/mongo.sh" status
    for p in backend frontend; do alive "$RUN/$p.pid" && echo "$p running (pid $(cat "$RUN/$p.pid"))" || echo "$p not running"; done
    ;;
  *) echo "usage: $0 start|stop|status"; exit 1 ;;
esac
