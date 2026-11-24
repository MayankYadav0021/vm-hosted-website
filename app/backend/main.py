import csv
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psutil

from app.backend import experiment_runner

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
HISTORY = RESULTS / "history"
HISTORY.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="AI-DevOps Benchmarking API",
    description="API for model benchmarking and optimization experiments.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

jobs = {}
jobs_lock = threading.Lock()

MODELS = [
    "distilbert/distilgpt2",
    "microsoft/DialoGPT-small",
    "microsoft/DialoGPT-medium",
    "microsoft/DialoGPT-large",
    "facebook/blenderbot-400M-distill",
    "google/pegasus-xsum",
]

WORKLOADS = [
    "chat_conversation",
    "content_generation",
    "technical_qa",
]


class ExperimentRequest(BaseModel):
    phase: str = Field(pattern=r"^(phase1|phase2_precision|phase2_batching|phase3_lora)$")
    model: str = Field(min_length=1, max_length=150)
    workload: str = "chat_conversation"
    precision: str = "fp32"
    batch_size: int = Field(default=1, ge=1, le=8)


def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def save_job(job):
    path = HISTORY / f"{job['id']}.json"
    path.write_text(json.dumps(job, indent=2), encoding="utf-8")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "AI-DevOps Benchmarking API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/system")
def system_metrics():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime_seconds = int(time.time() - psutil.boot_time())

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
        "uptime_seconds": uptime_seconds,
        "hostname": os.uname().nodename,
        "timestamp": datetime.now(timezone.utc).isoformat()
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
        "note": (
            "These are previously saved measurements. "
            "An empty result list means no summary rows were found."
        ),
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
        raise HTTPException(404, "Experiment not found")

    return job


@app.post("/api/experiments")
def create_experiment(request: ExperimentRequest):
    if request.model not in experiment_runner.ALLOWED_MODELS:
        raise HTTPException(400, "Unsupported model for experiment runner")

    if request.workload not in WORKLOADS:
        raise HTTPException(400, "Unsupported workload")

    if request.phase != "phase1" and request.model != "distilbert/distilgpt2":
        raise HTTPException(
            400,
            "Phase 2 and Phase 3 currently support only distilbert/distilgpt2."
        )

    try:
        return experiment_runner.start_job(request.phase, request.model)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except RuntimeError as exc:
        raise HTTPException(409, str(exc))


# FRONTEND_STATIC_MOUNT
FRONTEND_DIR = ROOT / "app" / "frontend"
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="frontend-css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="frontend-js")

@app.get("/", include_in_schema=False)
def serve_dashboard():
    return FileResponse(FRONTEND_DIR / "index.html")
