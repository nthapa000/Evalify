# mlflow_logger.py — Integration with MLflow for tracking evaluation runs.
# Logs metrics (scores, latency) and parameters (model versions, paper type).

from __future__ import annotations
import os
from typing import Dict, Any, Optional

# MLflow is optional — if it fails to import (e.g. numpy/pyarrow conflict when
# running outside the venv), evaluation still works; logging is just skipped.
try:
    import mlflow
    _MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5005")
    mlflow.set_tracking_uri(_MLFLOW_TRACKING_URI)
    _MLFLOW_OK = True
except Exception as _mlflow_err:
    _MLFLOW_OK = False
    print(f"⚠️  MLflow unavailable (import failed: {_mlflow_err.__class__.__name__}). "
          "Evaluation will run without experiment tracking. "
          "Start the backend using backend/start.sh to enable MLflow.")

def log_evaluation_run(
    submission_id: str,
    paper_id: str,
    paper_type: str,
    metrics: Dict[str, float],
    params: Dict[str, Any],
    artifacts: Optional[Dict[str, str]] = None,
    run_name: Optional[str] = None
):
    """
    Log a single evaluation run to MLflow.
    
    Args:
        submission_id: ID of the submission being evaluated
        paper_id: ID of the exam paper
        paper_type: Type of the paper (mcq, type2, type3)
        metrics: Dictionary of numeric scores and performance metrics
        params: Dictionary of model versions and hyperparameters
        artifacts: Optional dictionary of {artifact_name: file_path} to upload
        run_name: Optional display name for the run
    """
    if not _MLFLOW_OK:
        return  # skip silently when mlflow couldn't be imported

    try:
        experiment_name = f"evalify_{paper_type}"
        mlflow.set_experiment(experiment_name)
        
        with mlflow.start_run(run_name=run_name or f"eval_{submission_id}"):
            # 1. Log ID links
            mlflow.log_param("submission_id", submission_id)
            mlflow.log_param("paper_id", paper_id)
            mlflow.log_param("paper_type", paper_type)
            
            # 2. Log Model/Config Params
            for k, v in params.items():
                mlflow.log_param(k, v)
            
            # 3. Log Performance Metrics
            for k, v in metrics.items():
                mlflow.log_metric(k, v)
            
            # 4. Log Files (Images, JSON logs)
            if artifacts:
                for name, path in artifacts.items():
                    if os.path.exists(path):
                        mlflow.log_artifact(path, artifact_path=name)
                        
            print(f"📈 MLflow: Logged run for submission {submission_id}")
            
    except Exception as e:
        # We don't want MLflow logging issues to crash the evaluation pipeline
        print(f"⚠️ MLflow Warning: Could not log run: {str(e)}")
