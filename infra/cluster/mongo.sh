#!/bin/bash
# mongo.sh — Evalify's MongoDB on the cluster login node, in user space (no root, no Docker).
#
#   bash infra/cluster/mongo.sh init     # once: data dir, Evalify user with a random password, writes mongo.env
#   bash infra/cluster/mongo.sh start    # start (with password authentication)
#   bash infra/cluster/mongo.sh stop | status
#
# Listens on 127.0.0.1:27027 only; other users share the login node, so authentication is always on.
# Data:     /scratch/$USER/evalify/mongo-db             Log: /scratch/$USER/evalify/logs/mongod.log
# Password: /scratch/$USER/evalify/run/mongo.env (chmod 600, never in git) → MONGO_URI for the backend.
set -euo pipefail

BASE=/scratch/$USER/evalify
MONGOD=$(ls -d "$BASE"/mongodb/mongodb-linux-*/bin/mongod | head -1)
DATA=$BASE/mongo-db            # own folder; an older MongoDB 8.3 folder "mongo-data" (Nov 14) is left untouched
LOG=$BASE/logs/mongod.log
ENVF=$BASE/run/mongo.env
PORT=27027
PY=${PY:-/scratch/$USER/evalify/envs/backend/bin/python}

# Start mongod in the background; "$1" = extra flags (e.g. --auth)
_start() {
  mkdir -p "$DATA" "$(dirname "$LOG")" "$(dirname "$ENVF")"
  "$MONGOD" --dbpath "$DATA" --port $PORT --bind_ip 127.0.0.1 --logpath "$LOG" --logappend --fork \
            --pidfilepath "$BASE/run/mongod.pid" $1 >/dev/null
}

_running() { [ -f "$BASE/run/mongod.pid" ] && kill -0 "$(cat "$BASE/run/mongod.pid")" 2>/dev/null; }

case "${1:-status}" in
  init)
    if [ -f "$ENVF" ]; then echo "already initialised ($ENVF exists)"; exit 0; fi
    _running && { echo "stop mongod first"; exit 1; }
    _start ""                                              # first start without auth, only to create the users
    PW=$("$PY" -c "import secrets; print(secrets.token_urlsafe(24))")
    "$PY" - "$PW" <<'EOF'
import sys
from pymongo import MongoClient
pw = sys.argv[1]
c = MongoClient("mongodb://127.0.0.1:27027", serverSelectionTimeoutMS=10000)
c.admin.command("createUser", "evalify", pwd=pw, roles=[{"role": "readWrite", "db": "evalify_db"}])
print("user evalify created")
EOF
    umask 077
    printf 'MONGO_URI=mongodb://evalify:%s@127.0.0.1:%s/evalify_db?authSource=admin\nMONGO_DB_NAME=evalify_db\n' "$PW" $PORT > "$ENVF"
    chmod 600 "$ENVF"
    kill "$(cat "$BASE/run/mongod.pid")"; sleep 3
    _start "--auth"
    echo "MongoDB running with authentication on 127.0.0.1:$PORT; credentials in $ENVF"
    ;;
  start)
    _running && { echo "already running"; exit 0; }
    _start "--auth" && echo "MongoDB started on 127.0.0.1:$PORT"
    ;;
  stop)
    _running && kill "$(cat "$BASE/run/mongod.pid")" && echo "stopped" || echo "not running"
    ;;
  status)
    _running && echo "running (pid $(cat "$BASE/run/mongod.pid"), port $PORT, data $DATA)" || echo "not running"
    ;;
  *) echo "usage: $0 init|start|stop|status"; exit 1 ;;
esac
