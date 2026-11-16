#!/usr/bin/env bash
# serve_switch.sbatch — a GPU job whose serving profile can be changed without giving up the GPUs.
#
#   EVALIFY_ENDPOINTS_FILE=/scratch/$USER/evalify/run/endpoints-opt.json \
#   EVALIFY_LOG_DIR=/scratch/$USER/evalify/logs/opt \
#   sbatch --export=ALL infra/cluster/serve_switch.sbatch opt-lean
#
#   echo opt-batch > /scratch/$USER/evalify/run/opt_profile.txt     # switch: servers restart with that profile
#
# Used for the inference-optimisation experiments (INFERENCE_OPTIMIZATION.md): each step needs a vLLM restart
# with different flags, and re-queueing a Slurm job each time could lose the free GPUs.
#SBATCH --job-name=evalify-opt
#SBATCH --partition=mtech
#SBATCH --nodelist=cn07
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=1-12:00:00
#SBATCH --output=/scratch/%u/evalify/logs/serve-%j.out
set -uo pipefail

# Same environment as serve_models.sbatch
source "${EVALIFY_HOME:-$HOME/Evalify}/infra/cluster/env.sh"
export PATH="$VLLM_ENV/bin:$PATH" HF_HUB_OFFLINE=1
NV="$VLLM_ENV/lib/python3.12/site-packages/nvidia"
export LD_LIBRARY_PATH="$NV/cu13/lib:$NV/cudnn/lib:$NV/nccl/lib:$NV/cusparselt/lib:$NV/nvshmem/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CUDA_HOME="$NV/cu13" CUDA_DEVICE_ORDER=PCI_BUS_ID
export FLASHINFER_WORKSPACE_BASE="$EVALIFY_SCRATCH/cache" VLLM_USE_FLASHINFER_SAMPLER=0
mkdir -p "$EVALIFY_LOG_DIR"

# The profile to serve is read from this file; the job's argument is the first one
WANT="$EVALIFY_RUN_DIR/opt_profile.txt"
echo "${1:-wait}" > "$WANT"                     # "wait" = start nothing yet
echo "node=$(hostname) job=$SLURM_JOB_ID gpus=$CUDA_VISIBLE_DEVICES"
nvidia-smi --query-gpu=index,name,memory.total --format=csv

# Stop the current servers and wait until both GPUs are empty again
stop_servers() {
  [ -n "${PID:-}" ] && kill -TERM "$PID" 2>/dev/null && wait "$PID" 2>/dev/null
  pkill -TERM -u "$USER" -f "vllm serve .*--port 82[0-9][0-9]" 2>/dev/null
  for _ in $(seq 60); do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | sort -n | tail -1)
    [ "$used" -lt 2000 ] && return
    sleep 5
  done
  pkill -KILL -u "$USER" -f "vllm serve .*--port 82[0-9][0-9]" 2>/dev/null; sleep 10
}
trap 'stop_servers; rm -f "$EVALIFY_ENDPOINTS_FILE"; exit 0' TERM INT

# Watch the profile file; restart serve.py whenever it changes
CUR=""
while true; do
  NEXT=$(tr -d '[:space:]' < "$WANT")
  if [ "$NEXT" != "$CUR" ] && [ "$NEXT" != "wait" ]; then
    echo "$(date +%T) switching profile: '${CUR:-none}' -> '$NEXT'"
    stop_servers
    "$VLLM_ENV/bin/python" "$EVALIFY_HOME/infra/cluster/serve.py" "$NEXT" &
    PID=$!
    CUR="$NEXT"
  fi
  sleep 15
done
