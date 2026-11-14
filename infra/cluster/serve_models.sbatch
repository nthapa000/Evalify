#!/usr/bin/env bash
# serve_models.sbatch — start the vLLM servers for one serving profile on 2 GPUs (cn07).
# Usage: sbatch infra/cluster/serve_models.sbatch [profile]   (default: tier1-bakeoff)
#SBATCH --job-name=evalify-serve
#SBATCH --partition=mtech
#SBATCH --nodelist=cn07
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=1-12:00:00   # New: partition MaxTime is 1-12:00:00
#SBATCH --output=/scratch/%u/evalify/logs/serve-%j.out
set -euo pipefail

# New: profile name comes from the first argument (or PROFILE env var).
PROFILE="${1:-${PROFILE:-tier1-bakeoff}}"
# New: sbatch copies this script to a spool dir, so locate the repo through EVALIFY_HOME.
source "${EVALIFY_HOME:-$HOME/Evalify}/infra/cluster/env.sh"
PY="$VLLM_ENV/bin/python"
RUN_DIR="$EVALIFY_RUN_DIR"
LAUNCH="$RUN_DIR/launch-$PROFILE.sh"
WAIT_MAX=$((3 * 3600))   # New: max seconds to wait for model downloads and server startup

# New: read the profile from models.yaml and write a launch script with shell-quoted arguments.
"$PY" - "$PROFILE" "$LAUNCH" "$EVALIFY_HOME/infra/models.yaml" "$EVALIFY_ENDPOINTS_FILE" <<'EOF'
import json, shlex, sys, os
profile, out, reg_path, ep_path = sys.argv[1:5]
import yaml
reg = yaml.safe_load(open(reg_path))
prof = reg["profiles"].get(profile)
if prof is None:
    sys.exit(f"unknown profile {profile!r}; choose from {list(reg['profiles'])}")
lines = ["#!/usr/bin/env bash", "set -euo pipefail",
         # New: block until a server answers /health, so servers on one GPU start one at a time.
         "wait_health() { until curl -sf \"http://localhost:$2/health\" >/dev/null; do sleep 15; done; echo \"ready: $1 on port $2\"; }"]
endpoints = {}
for gpu, servers in prof["gpus"].items():
    for s in servers:
        m = reg["models"][s["model"]]
        args = m.get("vllm_args", [])
        lines.append(f"# {s['model']} on GPU {gpu} port {s['port']}")
        lines.append(
            f"CUDA_VISIBLE_DEVICES={gpu} vllm serve {shlex.quote(m['repo'])} "
            f"--revision {shlex.quote(m['revision'])} --served-model-name {shlex.quote(s['model'])} "
            f"--port {s['port']} --gpu-memory-utilization {s['mem']} "
            + " ".join(shlex.quote(a) for a in args)
            + f" > \"$EVALIFY_LOG_DIR/{s['model']}.log\" 2>&1 &"
        )
        lines.append(f"wait_health {s['model']} {s['port']}")
        endpoints[s["model"]] = {"url": f"http://localhost:{s['port']}/v1", "gpu": gpu,
                                 "repo": m["repo"], "revision": m["revision"]}
open(out, "w").write("\n".join(lines) + "\n")
json.dump({"profile": profile, "endpoints": endpoints}, open(ep_path + ".pending", "w"), indent=2)
EOF
chmod +x "$LAUNCH"

# New: wait until every model snapshot is complete (no .incomplete files, refs present).
"$PY" - "$PROFILE" "$EVALIFY_HOME/infra/models.yaml" "$WAIT_MAX" <<'EOF'
import os, sys, time, yaml, glob
profile, reg_path, wait_max = sys.argv[1], sys.argv[2], int(sys.argv[3])
reg = yaml.safe_load(open(reg_path))
names = {s["model"] for servers in reg["profiles"][profile]["gpus"].values() for s in servers}
hub = os.environ["HF_HUB_CACHE"]
def ready(name):
    m = reg["models"][name]
    d = os.path.join(hub, "models--" + m["repo"].replace("/", "--"))
    if not os.path.exists(os.path.join(d, "refs", m["revision"])):
        return False
    return not glob.glob(os.path.join(d, "blobs", "*.incomplete"))
t0 = time.time()
while True:
    missing = sorted(n for n in names if not ready(n))
    if not missing:
        print("all snapshots complete"); break
    if time.time() - t0 > wait_max:
        sys.exit(f"gave up waiting; still missing: {missing}")
    print(f"waiting for downloads: {missing}", flush=True)
    time.sleep(60)
EOF

# New: start servers; the launch script waits for each /health before starting the next on a GPU.
source "$LAUNCH"
echo "all servers for $PROFILE are healthy"
mv "$EVALIFY_ENDPOINTS_FILE.pending" "$EVALIFY_ENDPOINTS_FILE"
echo "endpoints written to $EVALIFY_ENDPOINTS_FILE"
# New: keep the job alive while the servers run.
wait
