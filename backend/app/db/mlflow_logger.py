# mlflow_logger.py — log evaluation runs and register model versions in MLflow.
# Every function is best effort: if MLflow is down, evaluation still succeeds.

from __future__ import annotations

import os
from typing import Any, Dict, Optional

# Connect once at import; disable tracking if mlflow is missing
try:
    import mlflow
    from mlflow.tracking import MlflowClient
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5005"))
    _MLFLOW_OK = True
except Exception as _err:
    _MLFLOW_OK = False
    print(f"⚠️  MLflow unavailable ({_err.__class__.__name__}); running without tracking.")


def log_evaluation_run(submission_id: str, paper_id: str, paper_type: str,
                       metrics: Dict[str, float], params: Dict[str, Any],
                       artifacts: Optional[Dict[str, str]] = None,
                       run_name: Optional[str] = None) -> Optional[str]:
    """Log one evaluation (params, metrics, files) under experiment evalify_<paper_type>; return run_id."""
    if not _MLFLOW_OK:
        return None
    try:
        mlflow.set_experiment(f"evalify_{paper_type}")
        with mlflow.start_run(run_name=run_name or f"eval_{submission_id}") as run:
            mlflow.log_params({"submission_id": submission_id, "paper_id": paper_id,
                               "paper_type": paper_type, **params})
            mlflow.log_metrics(metrics)
            for name, path in (artifacts or {}).items():
                if os.path.exists(path):
                    mlflow.log_artifact(path, artifact_path=name)
            return run.info.run_id
    except Exception as e:
        print(f"⚠️ MLflow: could not log run: {e}")
        return None


def register_model_version(model_name: str, run_id: str, artifact_path: str = "model",
                           description: str = "", tags: Optional[Dict[str, str]] = None) -> None:
    """Add a version of `model_name` to the Model Registry, linked to `run_id`."""
    if not _MLFLOW_OK or not run_id:
        return
    try:
        client = MlflowClient()
        # Create the registered model the first time (ignore "already exists")
        try:
            client.create_registered_model(model_name, description=f"Evalify — {model_name}")
        except Exception:
            pass
        client.create_model_version(name=model_name, source=f"runs:/{run_id}/{artifact_path}",
                                    run_id=run_id, description=description, tags=tags or {})
    except Exception as e:
        print(f"⚠️ MLflow Registry: could not register {model_name}: {e}")
