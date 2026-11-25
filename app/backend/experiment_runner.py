import json
import csv
import os
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[2]
PYTHON = ROOT / ".venv" / "bin" / "python"
HISTORY = ROOT / "results" / "history"
DETAILS = ROOT / "results" / "experiment_details"
LOGS = ROOT / "logs"

for folder in (HISTORY, DETAILS, LOGS):
    folder.mkdir(parents=True, exist_ok=True)

ALLOWED_MODELS = {
    "distilbert/distilgpt2",
    "microsoft/DialoGPT-small",
    "microsoft/DialoGPT-medium",
}

PHASES = {
    "phase1",
    "phase2_precision",
    "phase2_batching",
    "phase3_lora",
}

PHASE_SCRIPTS = {
    "phase1": ROOT / "phase1_cpu" / "phase1_cpu_experiment.py",
    "phase2_precision": ROOT / "phase2_cpu" / "precision_benchmark.py",
    "phase2_batching": ROOT / "phase2_cpu" / "batching_benchmark.py",
    "phase3_lora": ROOT / "phase3_lora" / "lora_benchmark.py",
}

PHASE_NAMES = {
    "phase1": "Model Benchmarking",
    "phase2_precision": "Precision Optimization",
    "phase2_batching": "Batching Optimization",
    "phase3_lora": "LoRA Fine-Tuning",
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



def publish_phase1_results(experiment_results_dir):
    """Publish successful Phase 1 measurements to central dashboard files."""
    source = Path(experiment_results_dir) / "phase1_model_summary.csv"
    central = ROOT / "results"
    central.mkdir(parents=True, exist_ok=True)

    if not source.is_file():
        raise RuntimeError("Phase 1 summary CSV was not generated.")

    with source.open(newline="", encoding="utf-8") as file:
        new_rows = list(csv.DictReader(file))

    summary_path = central / "phase1_model_summary.csv"
    existing = {}

    if summary_path.is_file():
        with summary_path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                if row.get("model"):
                    existing[row["model"]] = row

    for row in new_rows:
        if row.get("model"):
            existing[row["model"]] = row

    if existing:
        fields = list(dict.fromkeys(
            key for row in existing.values() for key in row
        ))
        with summary_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(existing.values())

    comparison_fields = [
        "model", "status", "avg_inference_time_sec",
        "avg_tokens_per_sec", "peak_ram_gb",
        "successful_requests", "total_requests",
    ]

    comparison_path = central / "phase1_model_comparison.csv"
    comparison_rows = {}

    if comparison_path.is_file():
        with comparison_path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                if row.get("model"):
                    comparison_rows[row["model"]] = row

    for row in new_rows:
        if row.get("model") and row.get("status") == "success":
            comparison_rows[row["model"]] = {
                key: row.get(key, "") for key in comparison_fields
            }

    with comparison_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=comparison_fields)
        writer.writeheader()
        writer.writerows(comparison_rows.values())

    return len(new_rows)


def publish_phase_results(phase, experiment_results_dir):
    filenames = {
        "phase2_precision": "precision_results.csv",
        "phase2_batching": "batching_results.csv",
        "phase3_lora": "lora_results.csv",
    }

    filename = filenames.get(phase)
    if filename is None:
        raise ValueError(f"Unsupported experiment result type: {phase}")

    source = Path(experiment_results_dir) / filename
    if not source.is_file():
        raise RuntimeError(f"Experiment result file was not generated: {filename}")

    with source.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        fields = reader.fieldnames
        rows = list(reader)

    if not fields:
        raise RuntimeError(f"Experiment result file has no CSV header: {filename}")

    central = ROOT / "results" / ("phase3" if phase == "phase3_lora" else "phase2")
    central.mkdir(parents=True, exist_ok=True)
    target = central / filename

    write_header = not target.is_file() or target.stat().st_size == 0

    with target.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def run_job(job_id, phase, model):
    global _active_job

    job = get_job(job_id)
    run_dir = DETAILS / job_id
    test_dir = run_dir / "test_1"
    log_path = LOGS / f"experiment_{job_id}.log"

    test_dir.mkdir(parents=True, exist_ok=True)

    results_dir = test_dir / "results"
    figures_dir = test_dir / "figures"
    logs_dir = test_dir / "logs"
    adapter_dir = test_dir / "adapter"

    for folder in (results_dir, figures_dir, logs_dir):
        folder.mkdir(parents=True, exist_ok=True)

    script = PHASE_SCRIPTS[phase]
    command = [str(PYTHON), str(script)]

    if phase == "phase1":
        command.extend(["--models", model])

    record = {
        "name": PHASE_NAMES[phase],
        "phase": phase,
        "status": "running",
        "exit_code": None,
        "result_files": [],
    }

    job["tests"] = [record]
    job["result_files"] = []
    job["status"] = "running"
    job["started_at"] = utc_now()
    job["updated_at"] = utc_now()
    job["message"] = f"{PHASE_NAMES[phase]} started."
    save_job(job)

    try:
        available_gib = psutil.virtual_memory().available / (1024 ** 3)

        if available_gib < 1.0:
            raise RuntimeError(
                f"Only {available_gib:.2f} GiB RAM is available; "
                "at least 1 GiB is required."
            )

        environment = os.environ.copy()
        environment["PYTHONUNBUFFERED"] = "1"
        environment["TOKENIZERS_PARALLELISM"] = "false"
        environment["AI_DEVOPS_RESULTS_DIR"] = str(results_dir)
        environment["AI_DEVOPS_FIGURES_DIR"] = str(figures_dir)
        environment["AI_DEVOPS_LOG_DIR"] = str(logs_dir)
        environment["AI_DEVOPS_ADAPTER_DIR"] = str(adapter_dir)

        with log_path.open("w", encoding="utf-8") as log:
            log.write(
                f"Experiment ID: {job_id}\n"
                f"Phase: {phase}\n"
                f"Model: {model}\n"
                f"Command: {' '.join(command)}\n"
            )
            log.flush()

            try:
                completed = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=environment,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=1800,
                    check=False,
                )

                record["exit_code"] = completed.returncode
                record["status"] = (
                    "completed" if completed.returncode == 0 else "failed"
                )

                if completed.returncode == 0 and phase == "phase1":
                    published = publish_phase1_results(results_dir)
                    log.write(
                        f"\\nPublished {published} Phase 1 model result(s) "
                        "to the central dashboard.\\n"
                    )
                    log.flush()
                elif completed.returncode == 0 and phase in {
                    "phase2_precision", "phase2_batching", "phase3_lora"
                }:
                    published = publish_phase_results(phase, results_dir)
                    log.write(
                        f"\\nPublished {published} experiment result row(s) "
                        "to the central dashboard.\\n"
                    )
                    log.flush()

            except subprocess.TimeoutExpired:
                record["status"] = "failed"
                record["error"] = "Experiment exceeded 30 minutes."

        for path in test_dir.rglob("*"):
            if path.is_file():
                relative = str(path.relative_to(ROOT))
                record["result_files"].append(relative)
                job["result_files"].append(relative)

        job["status"] = (
            "completed" if record["status"] == "completed" else "failed"
        )

        job["message"] = (
            "Experiment completed successfully."
            if job["status"] == "completed"
            else "Experiment failed. Check the saved execution log."
        )

    except Exception as exc:
        record["status"] = "failed"
        record["error"] = f"{type(exc).__name__}: {exc}"[:1000]
        job["status"] = "failed"
        job["message"] = record["error"]

    finally:
        job["log_file"] = str(log_path.relative_to(ROOT))
        job["finished_at"] = utc_now()
        job["updated_at"] = utc_now()
        save_job(job)

        with _lock:
            _active_job = None


def start_job(phase, model):
    global _active_job

    if phase not in PHASES:
        raise ValueError("Unsupported experiment phase.")

    if model not in ALLOWED_MODELS:
        raise ValueError("Unsupported model.")

    if phase != "phase1" and model != "distilbert/distilgpt2":
        raise ValueError(
            "Precision, batching and LoRA currently support "
            "distilbert/distilgpt2 only."
        )

    if not PYTHON.is_file():
        raise RuntimeError("Project virtual environment Python was not found.")

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
            "phase": phase,
            "experiment": PHASE_NAMES[phase],
            "model": model,
            "status": "queued",
            "message": f"{PHASE_NAMES[phase]} accepted and queued.",
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "finished_at": None,
            "exit_code": None,
            "log_file": None,
            "tests": [],
            "result_files": [],
            "additional_tests_supported": phase == "phase1",
        }

        _jobs[job_id] = job
        _active_job = job_id
        save_job(job)

        thread = threading.Thread(
            target=run_job,
            args=(job_id, phase, model),
            daemon=True,
        )
        thread.start()

    return job
