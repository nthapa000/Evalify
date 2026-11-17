# test_mlflow_logger.py — MLflow logging is best effort and must never slow evaluation down when MLflow is not running.

import pytest

from app.db import mlflow_logger as ml


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    """MLflow 'available' and the failure pause cleared before each test."""
    monkeypatch.setattr(ml, "_MLFLOW_OK", True)
    monkeypatch.setattr(ml, "_down_until", 0.0)


# Why: user report (17 Nov) — with MLflow down every sheet waited about 60 s for it; after one failed attempt the next
# calls must be skipped for a while instead of each waiting again
def test_failed_connection_pauses_logging(monkeypatch):
    calls = []

    def down(_name):
        calls.append(1)
        raise ConnectionError("localhost:5005 refused")
    monkeypatch.setattr(ml.mlflow, "set_experiment", down)
    args = dict(submission_id="s", paper_id="p", paper_type="mcq", metrics={}, params={})
    assert ml.log_evaluation_run(**args) is None
    assert ml.log_evaluation_run(**args) is None and ml.log_evaluation_run(**args) is None
    assert len(calls) == 1


# Why: after the pause MLflow is tried again, so tracking resumes by itself once MLflow is started
def test_logging_resumes_after_the_pause(monkeypatch):
    calls = []
    monkeypatch.setattr(ml.mlflow, "set_experiment", lambda _n: calls.append(1) or (_ for _ in ()).throw(ConnectionError("x")))
    args = dict(submission_id="s", paper_id="p", paper_type="mcq", metrics={}, params={})
    ml.log_evaluation_run(**args)
    monkeypatch.setattr(ml, "_down_until", 0.0)          # the pause is over
    ml.log_evaluation_run(**args)
    assert len(calls) == 2


# Why: a request to a dead MLflow must give up in seconds, not after the default minute of retries
def test_http_retries_are_short():
    import os
    assert os.environ["MLFLOW_HTTP_REQUEST_MAX_RETRIES"] == "0" and int(os.environ["MLFLOW_HTTP_REQUEST_TIMEOUT"]) <= 10
