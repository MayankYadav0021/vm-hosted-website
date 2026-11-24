import json
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / ".venv" / "bin" / "python"
HISTORY = ROOT / "results" / "history"
LOGS = ROOT / "logs"

HISTORY.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

ALLOWED_MODELS = {
    "distilbert/distilgpt2",
    "microsoft/DialoGPT-small",
    "microsoft/DialoGPT-medium",
}

EXPERIMENTS = {
    "phase1": ROOT / "phase1_cpu" / "phase1_cpu_experiment.py",
    "phase2_precision": ROOT / "phase2_cpu" / "precision_benchmark.py",
    "phase2_batching": ROOT / "phase2_cpu" / "batching_benchmark.py",
    "phase3_lora": ROOT / "phase3_lora" / "lora_benchmark.py",
}

_lock = threading.Lock()
_active_job = None
_jobs = {}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def save_job(job):
    path = HISTORY / f"{job['id']}.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(job, indent=2), encoding="utf-8")
    temporary.replace(path)


def load_history():
    records = {}
    for path in HISTORY.glob("*.json"):
        try:
            job = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(job, dict) and "id" in job:
                records[job["id"]] = job
        except (OSError, json.JSONDecodeError):
            continue
    return records


def get_job(job_id):
    with _lock:
        job = _jobs.get(job_id)

    if job is not None:
        return job

    path = HISTORY / f"{job_id}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    return None


def list_jobs():
    records = load_history()
    with _lock:
        records.update(_jobs)

    return sorted(
        records.values(),
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )


def build_command(kind, model):
    if kind not in EXPERIMENTS:
        raise ValueError("Unsupported experiment type.")

    if model not in ALLOWED_MODELS:
        raise ValueError("Unsupported model.")

    script = EXPERIMENTS[kind]

    if not script.is_file():
        raise RuntimeError(f"Experiment script not found: {script.name}")

    if not PYTHON.is_file():
        raise RuntimeError("Project virtual environment Python was not found.")

    if kind == "phase1":
        return [
            str(PYTHON),
            str(script),
            "--models",
            model,
        ]

    # These existing scripts currently use fixed experiment configurations.
    # They do not accept arbitrary models or shell arguments.
    if kind in {"phase2_precision", "phase2_batching", "phase3_lora"}:
        if model != "distilbert/distilgpt2":
            raise ValueError(
                "This experiment currently supports only distilbert/distilgpt2."
            )
        return [str(PYTHON), str(script)]

    raise ValueError("Unsupported experiment type.")


def run_job(job_id, kind, model, command):
    global _active_job

    job = get_job(job_id)
    log_path = LOGS / f"experiment_{job_id}.log"

    try:
        with _lock:
            job = _jobs[job_id]
            job["status"] = "running"
            job["message"] = "Experiment process started."
            job["started_at"] = utc_now()
            job["updated_at"] = utc_now()
            save_job(job)

        # Avoid starting another heavy model run when memory is already low.
        available_gib = psutil.virtual_memory().available / (1024 ** 3)
        if available_gib < 1.0:
            raise RuntimeError(
                f"Only {available_gib:.2f} GiB RAM is available; "
                "at least 1 GiB is required to start safely."
            )

        environment = os.environ.copy()
        environment["PYTHONUNBUFFERED"] = "1"
        environment["TOKENIZERS_PARALLELISM"] = "false"

        with log_path.open("w", encoding="utf-8") as log:
            log.write(f"Started: {utc_now()}\n")
            log.write(f"Experiment: {kind}\n")
            log.write(f"Model: {model}\n\n")
            log.flush()

            completed = subprocess.run(
                command,
                cwd=ROOT,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=1800,
                check=False,
            )

        with _lock:
            job = _jobs[job_id]
            job["exit_code"] = completed.returncode
            job["status"] = "completed" if completed.returncode == 0 else "failed"
            job["message"] = (
                "Experiment finished successfully."
                if completed.returncode == 0
                else "Experiment process returned an error. Check its log."
            )
            job["log_file"] = str(log_path.relative_to(ROOT))
            job["finished_at"] = utc_now()
            job["updated_at"] = utc_now()
            save_job(job)

    except subprocess.TimeoutExpired:
        with _lock:
            job = _jobs[job_id]
            job["status"] = "failed"
            job["message"] = "Experiment exceeded the 30-minute time limit."
            job["log_file"] = str(log_path.relative_to(ROOT))
            job["finished_at"] = utc_now()
            job["updated_at"] = utc_now()
            save_job(job)

    except Exception as exc:
        with _lock:
            job = _jobs[job_id]
            job["status"] = "failed"
            job["message"] = f"{type(exc).__name__}: {exc}"[:1000]
            job["log_file"] = str(log_path.relative_to(ROOT))
            job["finished_at"] = utc_now()
            job["updated_at"] = utc_now()
            save_job(job)

    finally:
        with _lock:
            _active_job = None


def start_job(kind, model):
    global _active_job

    command = build_command(kind, model)

    with _lock:
        if _active_job is not None:
            active = _jobs.get(_active_job, {})
            if active.get("status") in {"queued", "running"}:
                raise RuntimeError(
                    f"Experiment {active.get('id')} is already active."
                )

        job_id = str(uuid.uuid4())
        now = utc_now()

        job = {
            "id": job_id,
            "experiment": kind,
            "model": model,
            "status": "queued",
            "message": "Experiment accepted and waiting to start.",
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "finished_at": None,
            "exit_code": None,
            "log_file": None,
        }

        _jobs[job_id] = job
        _active_job = job_id
        save_job(job)

        thread = threading.Thread(
            target=run_job,
            args=(job_id, kind, model, command),
            daemon=True,
        )
        thread.start()

    return job
