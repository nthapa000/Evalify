# env.sh — shared environment for Evalify on the IIT Jodhpur cluster.
# Source this from every sbatch script and interactive shell:
#     source ~/Evalify/infra/cluster/env.sh
#
# Rule: everything heavy (conda env, HF weights, vLLM/torch/triton caches,
# pip cache, tmp) lives on /scratch. From cn07, reading /csehome is very slow
# (measured: 200 MB in ~130 s, `import torch` ~3 min), so nothing the GPU job
# loads may come from home.

export EVALIFY_HOME="${EVALIFY_HOME:-$HOME/Evalify}"
export EVALIFY_SCRATCH="${EVALIFY_SCRATCH:-/scratch/$USER/evalify}"

# Conda env with the pinned vLLM build (created by setup_vllm_env.sh)
export VLLM_ENV="$EVALIFY_SCRATCH/envs/vllm"
export VLLM_VERSION="${VLLM_VERSION:-0.32.0}"

# Model weights + caches
export HF_HOME="$EVALIFY_SCRATCH/hf"
export HF_HUB_CACHE="$HF_HOME/hub"
export HF_XET_HIGH_PERFORMANCE=1
export VLLM_CACHE_ROOT="$EVALIFY_SCRATCH/cache/vllm"
export TORCH_HOME="$EVALIFY_SCRATCH/cache/torch"
export TRITON_CACHE_DIR="$EVALIFY_SCRATCH/cache/triton"
export TORCHINDUCTOR_CACHE_DIR="$EVALIFY_SCRATCH/cache/inductor"
export XDG_CACHE_HOME="$EVALIFY_SCRATCH/cache/xdg"
export PIP_CACHE_DIR="$EVALIFY_SCRATCH/cache/pip"
export CONDA_PKGS_DIRS="$EVALIFY_SCRATCH/cache/conda_pkgs"
export APPTAINER_CACHEDIR="$EVALIFY_SCRATCH/cache/apptainer"
export TMPDIR="$EVALIFY_SCRATCH/tmp"

# Runtime state written by the serving job (endpoints file, logs)
export EVALIFY_RUN_DIR="$EVALIFY_SCRATCH/run"
export EVALIFY_ENDPOINTS_FILE="${EVALIFY_ENDPOINTS_FILE:-$EVALIFY_RUN_DIR/endpoints.json}"   # a second job can publish elsewhere
export EVALIFY_LOG_DIR="${EVALIFY_LOG_DIR:-$EVALIFY_SCRATCH/logs}"   # a second job keeps its own server logs

mkdir -p "$HF_HUB_CACHE" "$VLLM_CACHE_ROOT" "$TORCH_HOME" "$TRITON_CACHE_DIR" \
         "$TORCHINDUCTOR_CACHE_DIR" "$XDG_CACHE_HOME" "$PIP_CACHE_DIR" \
         "$CONDA_PKGS_DIRS" "$TMPDIR" "$EVALIFY_RUN_DIR" "$EVALIFY_LOG_DIR" 2>/dev/null

# Never phone home from the GPU job
export VLLM_NO_USAGE_STATS=1
export DO_NOT_TRACK=1
