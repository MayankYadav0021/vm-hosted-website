import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATASET = ROOT / "data" / "medicode_evaluation_dataset.json"
RESULTS = ROOT / "data" / "medicode_model_evaluation_results.json"

MODELS = [
    "qwen2.5-coder:3b",
    "starcoder2:3b",
    "codellama:7b",
]

REQUIRED_FIELDS = {
    "id",
    "category",
    "question",
    "expected_sources",
    "expected_keywords",
    "test_required",
}

def main():
    with open(DATASET, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print("=" * 60)
    print("MediCode Evaluation Preparation")
    print("=" * 60)

    print(f"Questions: {len(questions)}")

    categories = Counter(q["category"] for q in questions)

    print("\nCategories:")
    for category, count in categories.items():
        print(f"  {category}: {count}")

    # Validate records
    errors = []

    ids = []

    for q in questions:
        ids.append(q["id"])

        missing = REQUIRED_FIELDS - set(q.keys())

        if missing:
            errors.append(
                f"Question {q.get('id')}: missing fields {sorted(missing)}"
            )

        if not q["question"].strip():
            errors.append(
                f"Question {q.get('id')}: empty question"
            )

        if not q["expected_sources"]:
            errors.append(
                f"Question {q.get('id')}: no expected sources"
            )

    if len(ids) != len(set(ids)):
        errors.append("Duplicate question IDs detected.")

    print("\nValidation:")
    if errors:
        for error in errors:
            print("  ERROR:", error)
        raise SystemExit(1)

    print("  Dataset validation: PASS")

    # Create fresh result structure
    results = {
        "project": "MediCode AI",
        "dataset": "medicode_evaluation_dataset.json",
        "total_questions": len(questions),
        "evaluation_method": {
            "same_questions_for_all_models": True,
            "categories": list(categories.keys()),
            "metrics": [
                "correctness",
                "relevance",
                "retrieval_quality",
                "groundedness",
                "hallucination_rate",
                "code_test_pass_rate",
                "response_latency",
                "prompt_tokens",
                "output_tokens",
                "cpu_usage",
                "memory_usage"
            ]
        },
        "models": {}
    }

    for model in MODELS:
        results["models"][model] = {
            "status": "pending",
            "results": [],
            "summary": {}
        }

    with open(RESULTS, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nCreated: {RESULTS}")
    print("\nModels prepared:")
    for model in MODELS:
        print(f"  - {model}")

    print("\nLLM evaluation has NOT been started.")
    print("This step only prepares the evaluation framework.")


if __name__ == "__main__":
    main()
