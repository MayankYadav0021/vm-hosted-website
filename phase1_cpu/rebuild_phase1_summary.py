import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

SUMMARY_CSV = RESULTS / "phase1_model_summary.csv"
SUMMARY_JSON = RESULTS / "phase1_model_summary.json"

# Preserve existing model-loading measurements wherever available.
existing = {}

if SUMMARY_JSON.exists():
    try:
        with SUMMARY_JSON.open(encoding="utf-8") as f:
            for row in json.load(f):
                if row.get("model"):
                    existing[row["model"]] = row
    except (json.JSONDecodeError, OSError):
        pass

# These metadata values are defined in the original benchmark script.
import sys
sys.path.insert(0, str(ROOT / "phase1_cpu"))

try:
    from phase1_cpu_experiment import MODEL_PORTFOLIO
except Exception as exc:
    raise SystemExit(
        f"Could not import model metadata from the original script: {exc}"
    )

def mean(values):
    values = [
        float(v) for v in values
        if v not in (None, "") and math.isfinite(float(v))
    ]
    return sum(values) / len(values) if values else None

def maximum(values):
    values = [
        float(v) for v in values
        if v not in (None, "") and math.isfinite(float(v))
    ]
    return max(values) if values else None

summaries = []

for csv_path in sorted(RESULTS.glob("*_requests.csv")):
    with csv_path.open(newline="", encoding="utf-8") as f:
        requests = list(csv.DictReader(f))

    if not requests:
        print(f"Skipping empty file: {csv_path.name}")
        continue

    model_name = requests[0]["model"]
    previous = existing.get(model_name, {})
    metadata = MODEL_PORTFOLIO.get(model_name, {})

    times = [r.get("inference_time_sec") for r in requests]
    throughputs = [r.get("tokens_per_sec") for r in requests]
    output_tokens = [r.get("output_tokens") for r in requests]
    ram_after = [r.get("ram_after_inference_gb") for r in requests]
    ram_delta = [r.get("ram_delta_gb") for r in requests]

    successful = sum(
        1 for value in times
        if value not in (None, "")
        and math.isfinite(float(value))
    )

    total_output_tokens = sum(
        int(float(v)) for v in output_tokens
        if v not in (None, "") and math.isfinite(float(v))
    )

    result = {
        "model": model_name,
        "size_category": metadata.get(
            "size_category", requests[0].get("size_category", "unknown")
        ),
        "architecture": metadata.get(
            "architecture", requests[0].get("architecture", "unknown")
        ),
        "status": "success" if successful else "failed",
        "error": "",
        "parameters": previous.get("parameters"),
        "parameters_millions": previous.get("parameters_millions"),
        "estimated_fp32_size_gb": previous.get("estimated_fp32_size_gb"),
        "load_time_sec": previous.get("load_time_sec"),
        "ram_after_load_gb": previous.get("ram_after_load_gb"),
        "total_requests": len(requests),
        "successful_requests": successful,
        "avg_inference_time_sec": mean(times),
        "avg_tokens_per_sec": mean(throughputs),
        "total_output_tokens": total_output_tokens,
        "avg_output_tokens": mean(output_tokens),
        "peak_ram_gb": maximum(ram_after),
        "avg_ram_delta_gb": mean(ram_delta),
    }

    summaries.append(result)
    print(
        f"{model_name}: {successful}/{len(requests)} successful; "
        f"average inference={result['avg_inference_time_sec']}; "
        f"average throughput={result['avg_tokens_per_sec']}"
    )

if not summaries:
    raise SystemExit("No request CSV records found; summary not changed.")

fields = list(summaries[0].keys())

with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(summaries)

with SUMMARY_JSON.open("w", encoding="utf-8") as f:
    json.dump(summaries, f, indent=2, allow_nan=False)

print(f"\nRebuilt CSV:  {SUMMARY_CSV}")
print(f"Rebuilt JSON: {SUMMARY_JSON}")
print(f"Models summarized: {len(summaries)}")
print(
    "Note: loading metrics are preserved only where an existing summary "
    "contained them; missing values are left blank/null, not estimated."
)
