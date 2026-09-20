import csv
import json
import os
import sys
import time

from app.services.evaluation_service import EvaluationService

if len(sys.argv) != 2:
    print("Usage: python -m scripts.evaluate_one_model <model>")
    sys.exit(1)

model = sys.argv[1]

print(f"Evaluating ONLY: {model}")
print("One question at a time.")
print("Results are saved after every question.\n")

os.makedirs("results", exist_ok=True)

safe_name = model.replace(":", "_")
output_file = f"results/{safe_name}_evaluation.csv"

with open("data/evaluation_questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

service = EvaluationService()

fieldnames = [
    "question_id",
    "model",
    "status",
    "question",
    "answer",
    "retrieved_sources",
    "correctness_proxy",
    "relevance",
    "retrieval_quality",
    "hallucination_flag_proxy",
    "code_test_pass_rate",
    "latency_seconds",
    "prompt_tokens",
    "output_tokens",
    "memory_delta_mb",
    "error"
]

completed = {}

if os.path.exists(output_file):
    with open(output_file, "r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            completed[int(row["question_id"])] = row

if completed:
    print(f"Found {len(completed)} previously saved results.")
    print("Those questions will be skipped.\n")

with open(
    output_file,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for row in completed.values():
        writer.writerow(row)

    f.flush()

    for i, item in enumerate(questions, 1):

        if item["id"] in completed:
            print(
                f"[{i}/25] Question {item['id']} already saved - skipping",
                flush=True
            )
            continue

        print(
            f"[{i}/25] Question {item['id']}...",
            flush=True
        )

        start = time.perf_counter()

        try:
            row = service.evaluate_question(model, item)

        except Exception as e:
            row = {
                "question_id": item["id"],
                "model": model,
                "status": "failed",
                "question": item["question"],
                "answer": "",
                "retrieved_sources": "",
                "correctness_proxy": 0,
                "relevance": 0,
                "retrieval_quality": 0,
                "hallucination_flag_proxy": 0,
                "code_test_pass_rate": None,
                "latency_seconds": round(
                    time.perf_counter() - start,
                    3
                ),
                "prompt_tokens": 0,
                "output_tokens": 0,
                "memory_delta_mb": 0,
                "error": str(e)
            }

        for key in fieldnames:
            row.setdefault(key, "")

        writer.writerow(row)
        f.flush()

        print(
            f"    {row['status']} | "
            f"latency={row.get('latency_seconds', 0)}s",
            flush=True
        )

print(f"\nSaved: {output_file}")
print("Evaluation finished.")
