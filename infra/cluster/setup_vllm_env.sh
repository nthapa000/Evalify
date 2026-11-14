#!/usr/bin/env bash
# setup_vllm_env.sh — create the pinned vLLM conda env on /scratch.
# Run once on the login node (it has internet):
#     bash ~/Evalify/infra/cluster/setup_vllm_env.sh
#
# Why a conda env instead of the vllm-openai container: Apptainer/Singularity
# is not installed on this cluster. The pin (VLLM_VERSION in env.sh) plays the
# role of "pin a known-good container".
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

if [ ! -x "$VLLM_ENV/bin/python" ]; then
  conda create -y -p "$VLLM_ENV" python=3.12 pip
fi
PY="$VLLM_ENV/bin/python"

"$PY" -m pip install --upgrade pip uv
# uv resolves the torch/CUDA wheels much faster than pip
"$PY" -m uv pip install --python "$PY" \
  "vllm==${VLLM_VERSION}" \
  huggingface_hub \
  pyyaml requests

"$PY" - <<'EOF'
import vllm, torch, transformers
print("vllm", vllm.__version__, "| torch", torch.__version__, "| cuda", torch.version.cuda,
      "| transformers", transformers.__version__)
from vllm.model_executor.models.registry import ModelRegistry
need = ["Qwen3_5ForConditionalGeneration", "Gemma4ForConditionalGeneration",
        "PaddleOCRVLForConditionalGeneration", "GlmOcrForConditionalGeneration",
        "Qwen2_5_VLForConditionalGeneration", "GptOssForCausalLM"]
have = set(ModelRegistry.get_supported_archs())
for a in need:
    print(f"  {'OK ' if a in have else 'MISSING'} {a}")
EOF
echo "✅ vLLM env ready at $VLLM_ENV"
