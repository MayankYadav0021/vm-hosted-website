import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

from app.backend import experiment_runner, model_advisor
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
HISTORY = RESULTS / "history"
DETAILS = RESULTS / "experiment_details"
FRONTEND_DIR = ROOT / "app" / "frontend"

HISTORY.mkdir(parents=True, exist_ok=True)
DETAILS.mkdir(parents=True, exist_ok=True)


def load_env_file():
    env_path = ROOT / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(
            key.strip(),
            value.strip().strip('"').strip("'")
        )


load_env_file()

app = FastAPI(
    title="AI-DevOps Benchmarking API",
    description="Model benchmarking, experiment history and AI model research.",
    version="2.0.0",
)

MODELS = sorted(experiment_runner.ALLOWED_MODELS)

WORKLOADS = [
    "chat_conversation",
    "content_generation",
    "technical_qa",
]


class ExperimentRequest(BaseModel):
    phase: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=150)
    workload: str = "chat_conversation"


def read_csv(path: Path):
    if not path.is_file():
        return []

    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def authenticate(token):
    expected = os.environ.get("EXPERIMENT_API_TOKEN", "")

    if not expected or not token:
        raise HTTPException(401, "Experiment authentication required.")

    if not __import__("hmac").compare_digest(token, expected):
        raise HTTPException(403, "Invalid experiment token.")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "AI-DevOps Benchmarking API",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/system")
def system_metrics():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "cpu_percent": psutil.cpu_percent(interval=0.2),
        "cpu_count": psutil.cpu_count(),
        "memory_percent": memory.percent,
        "memory_total_gb": round(memory.total / (1024 ** 3), 2),
        "memory_used_gb": round(memory.used / (1024 ** 3), 2),
        "memory_available_gb": round(memory.available / (1024 ** 3), 2),
        "disk_percent": disk.percent,
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
        "uptime_seconds": int(time.time() - psutil.boot_time()),
        "hostname": os.uname().nodename,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/models")
def list_models():
    return {"models": MODELS}


@app.get("/api/workloads")
def list_workloads():
    return {"workloads": WORKLOADS}


@app.get("/api/results/phase1")
def phase1_results():
    path = RESULTS / "phase1_model_summary.csv"
    return {
        "results": read_csv(path),
        "source": str(path.relative_to(ROOT)),
        "note": "Previously saved Phase 1 measurements.",
    }


@app.get("/api/results")
def all_results():
    return {
        "phase1": read_csv(RESULTS / "phase1_model_summary.csv"),
        "phase1_model_comparison": read_csv(
            RESULTS / "phase1_model_comparison.csv"
        ),
        "phase2_precision": read_csv(
            RESULTS / "phase2" / "precision_results.csv"
        ),
        "phase2_batching": read_csv(
            RESULTS / "phase2" / "batching_results.csv"
        ),
        "phase3_lora": read_csv(
            RESULTS / "phase3" / "lora_results.csv"
        ),
    }


@app.get("/api/experiments")
def experiment_history():
    return {"experiments": experiment_runner.list_jobs()}


@app.get("/api/experiments/{experiment_id}")
def experiment_status(experiment_id: str):
    job = experiment_runner.get_job(experiment_id)

    if job is None:
        raise HTTPException(404, "Experiment not found.")

    return job


@app.get("/api/experiments/{experiment_id}/results")
def experiment_results(experiment_id: str):
    job = experiment_runner.get_job(experiment_id)

    if job is None:
        raise HTTPException(404, "Experiment not found.")

    output = {}

    for relative_path in job.get("result_files", []):
        path = (ROOT / relative_path).resolve()

        if not path.is_relative_to(DETAILS.resolve()):
            continue

        if not path.is_file():
            continue

        if path.suffix.lower() == ".csv":
            output[relative_path] = read_csv(path)
        elif path.suffix.lower() == ".json":
            try:
                output[relative_path] = json.loads(
                    path.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError):
                output[relative_path] = None

    log_file = job.get("log_file")
    if log_file:
        log_path = (ROOT / log_file).resolve()
        if log_path.is_relative_to((ROOT / "logs").resolve()):
            if log_path.is_file():
                output["log"] = log_path.read_text(
                    encoding="utf-8",
                    errors="replace"
                )[-30000:]

    return {
        "experiment_id": experiment_id,
        "model": job.get("model"),
        "status": job.get("status"),
        "results": output,
    }


@app.get("/api/experiments/{experiment_id}/files/{file_path:path}")
def experiment_file(experiment_id: str, file_path: str):
    job = experiment_runner.get_job(experiment_id)

    if job is None:
        raise HTTPException(404, "Experiment not found.")

    if file_path not in job.get("result_files", []):
        raise HTTPException(404, "Experiment file not found.")

    experiment_dir = (DETAILS / experiment_id).resolve()
    target = (ROOT / file_path).resolve()

    if not target.is_relative_to(experiment_dir):
        raise HTTPException(404, "Experiment file not found.")

    if not target.is_file():
        raise HTTPException(404, "Experiment file not found.")

    if target.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(404, "Unsupported image format.")

    return FileResponse(target)


class AdvisorRequest(BaseModel):
    query: str = Field(min_length=5, max_length=2000)


@app.get("/api/advisor/benchmarks")
def advisor_benchmarks():
    return {"models": model_advisor.read_benchmarks()}


@app.post("/api/advisor/recommend")
def advisor_recommend(request: AdvisorRequest):
    try:
        return model_advisor.recommend_models(request.query)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/api/experiments")
def create_experiment(
    request: ExperimentRequest,
    x_experiment_token: str | None = Header(default=None),
):
    authenticate(x_experiment_token)

    if request.phase not in experiment_runner.PHASES:
        raise HTTPException(400, "Unsupported experiment phase.")

    if request.model not in experiment_runner.ALLOWED_MODELS:
        raise HTTPException(400, "Unsupported model.")

    if request.workload not in WORKLOADS:
        raise HTTPException(400, "Unsupported workload.")

    try:
        return experiment_runner.start_job(request.phase, request.model)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except RuntimeError as exc:
        raise HTTPException(409, str(exc))


app.mount(
    "/css",
    StaticFiles(directory=FRONTEND_DIR / "css"),
    name="frontend-css",
)
app.mount(
    "/js",
    StaticFiles(directory=FRONTEND_DIR / "js"),
    name="frontend-js",
)


@app.get("/", include_in_schema=False)
def serve_dashboard():
    return FileResponse(FRONTEND_DIR / "index.html")
