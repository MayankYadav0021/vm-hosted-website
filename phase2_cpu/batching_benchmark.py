import csv
import gc
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "phase2"
LOGS = ROOT / "logs"

RESULTS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "distilbert/distilgpt2"
BATCH_SIZES = [1, 2, 4, 8]

PROMPTS = [
    "Explain artificial intelligence in simple terms.",
    "What is cloud computing and why is it useful?",
    "Describe three applications of machine learning.",
    "Explain how neural networks learn.",
    "What is the purpose of a database?",
    "Describe the benefits of automation.",
    "Explain what a transformer model does.",
    "What is the difference between AI and machine learning?",
]

OUTPUT_CSV = RESULTS / "batching_results.csv"
LOG_FILE = LOGS / "phase2_batching.log"

FIELDS = [
    "timestamp",
    "model",
    "device",
    "precision",
    "batch_size",
    "status",
    "error",
    "load_time_sec",
    "avg_batch_latency_sec",
    "total_inference_time_sec",
    "total_output_tokens",
    "avg_tokens_per_sec",
    "peak_process_ram_gb",
    "available_system_ram_gb",
    "successful_requests",
    "total_requests",
]


def log(message):
    line = f"[{datetime.now(timezone.utc).isoformat()}] {message}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def append_result(row):
    with OUTPUT_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if OUTPUT_CSV.stat().st_size == 0:
            writer.writeheader()
        writer.writerow(row)


def run_batch(model, tokenizer, batch_size):
    process = psutil.Process(os.getpid())

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": MODEL_NAME,
        "device": "cpu",
        "precision": "fp32",
        "batch_size": batch_size,
        "status": "failed",
        "error": "",
        "load_time_sec": "",
        "avg_batch_latency_sec": "",
        "total_inference_time_sec": "",
        "total_output_tokens": 0,
        "avg_tokens_per_sec": "",
        "peak_process_ram_gb": "",
        "available_system_ram_gb": "",
        "successful_requests": 0,
        "total_requests": 0,
    }

    try:
        if psutil.virtual_memory().available < 0.8 * (1024 ** 3):
            raise RuntimeError("Less than 0.8 GiB system RAM available.")

        durations = []
        total_tokens = 0
        peak_ram = process.memory_info().rss / (1024 ** 3)
        start_total = time.perf_counter()

        for offset in range(0, len(PROMPTS), batch_size):
            prompts = PROMPTS[offset:offset + batch_size]
            inputs = tokenizer(
                prompts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=128,
            )

            # Keep generation length small to protect the 4 GiB instance.
            start = time.perf_counter()

            with torch.inference_mode():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=12,
                    do_sample=False,
                    pad_token_id=tokenizer.pad_token_id,
                )

            elapsed = time.perf_counter() - start
            durations.append(elapsed)

            # Count generated tokens after the padded input width.
            input_width = inputs["input_ids"].shape[1]
            for i in range(outputs.shape[0]):
                generated = outputs[i, input_width:].tolist()
                token_count = 0

                for token_id in generated:
                    if token_id == tokenizer.eos_token_id:
                        token_count += 1
                        break
                    if token_id == tokenizer.pad_token_id:
                        break
                    token_count += 1

                total_tokens += token_count

            row["successful_requests"] += len(prompts)
            peak_ram = max(
                peak_ram,
                process.memory_info().rss / (1024 ** 3),
            )

            log(
                f"batch={batch_size}: processed "
                f"{row['successful_requests']}/{len(PROMPTS)} prompts"
            )

        total_elapsed = time.perf_counter() - start_total

        row["status"] = "success"
        row["total_requests"] = len(PROMPTS)
        row["avg_batch_latency_sec"] = round(
            sum(durations) / len(durations), 6
        )
        row["total_inference_time_sec"] = round(total_elapsed, 6)
        row["total_output_tokens"] = total_tokens
        row["avg_tokens_per_sec"] = round(
            total_tokens / total_elapsed if total_elapsed else 0, 6
        )
        row["peak_process_ram_gb"] = round(peak_ram, 6)
        row["available_system_ram_gb"] = round(
            psutil.virtual_memory().available / (1024 ** 3), 6
        )

    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"[:1000]
        row["total_requests"] = len(PROMPTS)
        row["available_system_ram_gb"] = round(
            psutil.virtual_memory().available / (1024 ** 3), 6
        )
        log(f"batch={batch_size} failed: {row['error']}")

    append_result(row)
    log(
        f"batch={batch_size}: status={row['status']}, "
        f"throughput={row['avg_tokens_per_sec']}"
    )


def main():
    torch.set_num_threads(2)

    log(f"Starting batching experiment for {MODEL_NAME}")
    log(f"Available RAM: {psutil.virtual_memory().available / (1024 ** 3):.2f} GiB")

    tokenizer = None
    model = None

    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"

        load_start = time.perf_counter()
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            dtype=torch.float32,
            low_cpu_mem_usage=True,
        )
        model.eval()
        load_time = time.perf_counter() - load_start

        log(f"Model loaded in {load_time:.4f} seconds")

        # Run in ascending order; stop if system RAM becomes critically low.
        for batch_size in BATCH_SIZES:
            if psutil.virtual_memory().available < 0.8 * (1024 ** 3):
                log("Stopping because available RAM is below 0.8 GiB.")
                break

            run_batch(model, tokenizer, batch_size)

    finally:
        del model
        del tokenizer
        gc.collect()

    log(f"Batching results saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
