# mlflow_logger.py — Integration with MLflow for tracking evaluation runs
# and registering model versions in the MLflow Model Registry.

from __future__ import annotations
import os
from typing import Dict, Any, Optional

try:
    import mlflow
    from mlflow.tracking import MlflowClient
    _MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5005")
    mlflow.set_tracking_uri(_MLFLOW_TRACKING_URI)
    _MLFLOW_OK = True
except Exception as _mlflow_err:
    _MLFLOW_OK = False
    print(f"⚠️  MLflow unavailable (import failed: {_mlflow_err.__class__.__name__}). "
          "Evaluation will run without experiment tracking.")


def log_evaluation_run(
    submission_id: str,
    paper_id: str,
    paper_type: str,
    metrics: Dict[str, float],
    params: Dict[str, Any],
    artifacts: Optional[Dict[str, str]] = None,
    run_name: Optional[str] = None,
) -> Optional[str]:
    """
    Log a single evaluation run to MLflow.

    Returns the MLflow run_id on success, None on failure.

    params should include:
      vision_model  — Ollama model used for OCR (e.g. "llama3.2-vision:11b")
      grader_model  — Ollama model used for LLM grading (same or different)
      engine        — "opencv_omr" | "ollama_vision"
      sheet_type    — "omr" | "handwritten"
      ollama_mode   — "real" | "stub"
    """
    if not _MLFLOW_OK:
        return None

    try:
        experiment_name = f"evalify_{paper_type}"
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(run_name=run_name or f"eval_{submission_id}") as run:
            mlflow.log_param("submission_id", submission_id)
            mlflow.log_param("paper_id", paper_id)
            mlflow.log_param("paper_type", paper_type)

            for k, v in params.items():
                mlflow.log_param(k, v)

            for k, v in metrics.items():
                mlflow.log_metric(k, v)

            if artifacts:
                for name, path in artifacts.items():
                    if os.path.exists(path):
                        mlflow.log_artifact(path, artifact_path=name)

            run_id = run.info.run_id
            print(f"📈 MLflow: logged run {run_id} for submission {submission_id}")
            return run_id

    except Exception as e:
        print(f"⚠️ MLflow: could not log run: {e}")
        return None


def register_model_version(
    model_name: str,
    run_id: str,
    artifact_path: str = "model",
    description: str = "",
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """
    Register (or update) a model version in the MLflow Model Registry.

    This is the MLOps way to track which model version is in use.
    After registering, you can promote versions through:
      None → Staging → Production → Archived

    Args:
        model_name    — Registry name, e.g. "evalify-vision-ocr"
        run_id        — The MLflow run_id returned by log_evaluation_run()
        artifact_path — Path inside the run's artifact store (default "model")
        description   — Human-readable note about this version
        tags          — Extra key/value tags for the version

    Example:
        register_model_version(
            model_name   = "evalify-vision-ocr",
            run_id       = run_id,
            description  = "llama3.2-vision:11b — baseline evaluation",
            tags         = {"ollama_tag": "llama3.2-vision:11b", "hw": "V100x2"},
        )
    """
    if not _MLFLOW_OK or not run_id:
        return

    try:
        client = MlflowClient()
        model_uri = f"runs:/{run_id}/{artifact_path}"

        # Create the registered model if it doesn't exist yet
        try:
            client.create_registered_model(
                name=model_name,
                description=f"Evalify evaluation model — {model_name}",
            )
        except Exception:
            pass  # already exists — that's fine

        # Create a new version
        version = client.create_model_version(
            name=model_name,
            source=model_uri,
            run_id=run_id,
            description=description,
            tags=tags or {},
        )
        print(f"📦 MLflow Registry: {model_name} v{version.version} registered "
              f"(run {run_id})")

    except Exception as e:
        print(f"⚠️ MLflow Registry: could not register model version: {e}")


def get_production_model(model_name: str) -> Optional[str]:
    """
    Return the Ollama model tag that is currently marked Production
    in the MLflow Model Registry for the given registered model name.

    Returns the 'ollama_tag' version tag, or None if not found.

    Example:
        tag = get_production_model("evalify-vision-ocr")
        # → "llama3.2-vision:11b"
    """
    if not _MLFLOW_OK:
        return None

    try:
        client = MlflowClient()
        versions = client.get_latest_versions(model_name, stages=["Production"])
        if versions:
            return versions[0].tags.get("ollama_tag")
    except Exception:
        pass
    return None
