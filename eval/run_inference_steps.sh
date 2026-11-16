#!/usr/bin/env bash
# run_inference_steps.sh — measure serving profiles one after another on the switchable GPU job.
#
#   bash eval/run_inference_steps.sh opt-lean opt-swap opt-batch opt-fp8kv
#   EXTRA="--workloads data-science" bash eval/run_inference_steps.sh opt-batch
#
# For each profile: ask serve_switch.sbatch to load it, wait until its 3 servers are up, then run
# eval/exp_inference.py with --config <profile>. See INFERENCE_OPTIMIZATION.md.
set -uo pipefail
cd "$(dirname "$0")/.."
RUN=/scratch/$USER/evalify/run
EP=$RUN/endpoints-opt.json
PY=/scratch/$USER/evalify/envs/backend/bin/python

for prof in "$@"; do
  echo "$(date +%T) profile $prof: switching"
  echo "$prof" > "$RUN/opt_profile.txt"
  sleep 30
  # Ready = endpoints file written for this profile with all of its servers (allow 40 min for kernel compiles)
  want=$($PY -c "import yaml,sys;print(len(yaml.safe_load(open('infra/models.yaml'))['profiles']['$prof']))")
  for _ in $(seq 240); do
    got=$($PY -c "import json;d=json.load(open('$EP'));print(len(d['models']) if d.get('profile')=='$prof' else 0)" 2>/dev/null || echo 0)
    [ "$got" = "$want" ] && break
    sleep 10
  done
  [ "$got" = "$want" ] || { echo "$(date +%T) profile $prof: servers not up ($got/$want), skipping"; continue; }
  echo "$(date +%T) profile $prof: ready, measuring"
  $PY eval/exp_inference.py run --config "${CONFIG:-$prof}" --endpoints "$EP" ${EXTRA:-}   # CONFIG: name for client-side variants
done
echo "$(date +%T) done: $*"
