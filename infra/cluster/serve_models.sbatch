#!/usr/bin/env bash
# serve_models.sbatch — run the vLLM servers of one serving profile on 2 GPUs of cn07.
#
#   sbatch infra/cluster/serve_models.sbatch                  # tier1-bakeoff (all candidates)
#   sbatch infra/cluster/serve_models.sbatch tier1            # production shape
#   EVALIFY_AFTER_READY="bash eval/run_bakeoff.sh" sbatch --export=ALL infra/cluster/serve_models.sbatch
#
# Endpoints appear in $EVALIFY_ENDPOINTS_FILE (on /scratch) as servers come up.
#SBATCH --job-name=evalify-serve
#SBATCH --partition=mtech
#SBATCH --nodelist=cn07
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=1-12:00:00
#SBATCH --output=/scratch/%u/evalify/logs/serve-%j.out
set -euo pipefail

# sbatch runs a spooled copy of this file, so find the repo via EVALIFY_HOME
source "${EVALIFY_HOME:-$HOME/Evalify}/infra/cluster/env.sh"

# vllm from the pinned env; weights only from the local cache (no downloads on the GPU node)
export PATH="$VLLM_ENV/bin:$PATH"
export HF_HUB_OFFLINE=1

# CUDA 13 runtime libs ship as pip wheels; the JIT compiler (NVRTC) must find them
NV="$VLLM_ENV/lib/python3.12/site-packages/nvidia"
export LD_LIBRARY_PATH="$NV/cu13/lib:$NV/cudnn/lib:$NV/nccl/lib:$NV/cusparselt/lib:$NV/nvshmem/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CUDA_HOME="$NV/cu13"

echo "node=$(hostname) job=$SLURM_JOB_ID gpus=$CUDA_VISIBLE_DEVICES"
nvidia-smi --query-gpu=index,name,memory.total,memory.used --format=csv

# serve.py maps profile GPUs 0/1 onto the devices Slurm allocated
exec "$VLLM_ENV/bin/python" "$EVALIFY_HOME/infra/cluster/serve.py" "${1:-tier1-bakeoff}"
