import csv
import gc
import os
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import psutil
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(os.environ.get("AI_DEVOPS_RESULTS_DIR", str(ROOT / "results" / "phase2")))
LOGS = Path(os.environ.get("AI_DEVOPS_LOG_DIR", str(ROOT / "logs")))

RESULTS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "distilbert/distilgpt2"
PROMPTS = [
    "Explain artificial intelligence in simple terms.",
    "What is cloud computing and why is it useful?",
    "Describe three applications of machine learning.",
]

OUTPUT_CSV = RESULTS / "precision_results.csv"
LOG_FILE = LOGS / "phase2_precision.log"

FIELDS = [
    "timestamp",
    "model",
    "device",
    "precision",
    "status",
    "error",
    "load_time_sec",
    "parameters",
    "avg_inference_time_sec",
    "avg_tokens_per_sec",
    "peak_process_ram_gb",
    "available_system_ram_gb",
    "successful_requests",
    "total_requests",
]


def write_log(message):
    timestamp = datetime.now(timezone.utc).isoformat()
    line = f"[{timestamp}] {message}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def append_result(row):
    exists = OUTPUT_CSV.exists()
    with OUTPUT_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not exists or OUTPUT_CSV.stat().st_size == 0:
            writer.writeheader()
        writer.writerow(row)


def run_precision(precision):
    process = psutil.Process(os.getpid())
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": MODEL_NAME,
        "device": "cpu",
        "precision": precision,
        "status": "failed",
        "error": "",
        "load_time_sec": "",
        "parameters": "",
        "avg_inference_time_sec": "",
        "avg_tokens_per_sec": "",
        "peak_process_ram_gb": "",
        "available_system_ram_gb": "",
        "successful_requests": 0,
        "total_requests": len(PROMPTS),
    }

    model = None
    tokenizer = None

    try:
        if psutil.virtual_memory().available < 1.0 * (1024 ** 3):
            raise RuntimeError(
                "Insufficient available RAM to start safely; "
                "at least 1 GiB is required."
            )

        dtype = torch.float32 if precision == "fp32" else torch.float16
        write_log(f"Starting {precision} experiment for {MODEL_NAME}")

        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        start_load = time.perf_counter()

        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=dtype,
            low_cpu_mem_usage=True,
        )
        model.eval()

        row["load_time_sec"] = round(
            time.perf_counter() - start_load, 6
        )
        row["parameters"] = sum(p.numel() for p in model.parameters())

        durations = []
        throughputs = []
        peak_ram = process.memory_info().rss / (1024 ** 3)

        for index, prompt in enumerate(PROMPTS, start=1):
            inputs = tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=128,
            )

            start = time.perf_counter()

            with torch.inference_mode():
                output = model.generate(
                    **inputs,
                    max_new_tokens=16,
                    do_sample=False,
                    pad_token_id=tokenizer.pad_token_id,
                )

            elapsed = time.perf_counter() - start
            input_count = inputs["input_ids"].shape[1]
            output_count = max(0, output.shape[1] - input_count)

            durations.append(elapsed)
            throughputs.append(
                output_count / elapsed if elapsed > 0 else 0.0
            )
            row["successful_requests"] += 1

            peak_ram = max(
                peak_ram,
                process.memory_info().rss / (1024 ** 3),
            )

            write_log(
                f"{precision}: request {index}/{len(PROMPTS)} "
                f"completed in {elapsed:.4f}s; "
                f"generated tokens={output_count}"
            )

        row["status"] = "success"
        row["avg_inference_time_sec"] = round(
            sum(durations) / len(durations), 6
        )
        row["avg_tokens_per_sec"] = round(
            sum(throughputs) / len(throughputs), 6
        )
        row["peak_process_ram_gb"] = round(peak_ram, 6)
        row["available_system_ram_gb"] = round(
            psutil.virtual_memory().available / (1024 ** 3), 6
        )

        write_log(
            f"{precision} completed successfully: "
            f"average latency={row['avg_inference_time_sec']}s"
        )

    except Exception as exc:
        row["status"] = "unsupported_or_failed"
        row["error"] = f"{type(exc).__name__}: {exc}"[:1000]
        row["available_system_ram_gb"] = round(
            psutil.virtual_memory().available / (1024 ** 3), 6
        )
        write_log(f"{precision} failed: {row['error']}")

    finally:
        del model
        del tokenizer
        gc.collect()

    append_result(row)
    return row


def main():
    torch.set_num_threads(2)

    write_log("Phase 2 precision benchmark started")
    write_log(f"PyTorch version: {torch.__version__}")
    write_log(f"CUDA available: {torch.cuda.is_available()}")
    write_log(
        f"Available system RAM: "
        f"{psutil.virtual_memory().available / (1024 ** 3):.2f} GiB"
    )

    # Run sequentially so both model copies are never held simultaneously.
    for precision in ("fp32", "fp16"):
        result = run_precision(precision)
        print(
            f"\nRESULT: {precision} -> {result['status']}",
            flush=True,
        )

    write_log(f"Results saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
