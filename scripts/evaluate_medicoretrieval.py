import json
import time
from statistics import mean

from app.config import EMBED_MODEL
from app.services.ollama_service import OllamaService
from app.services.retrieval_service import RetrievalService

QUESTIONS = "data/medicode_evaluation_questions.json"
OUTPUT = "data/medicode_retrieval_results.json"

with open(QUESTIONS, encoding="utf-8") as f:
    questions = json.load(f)

ollama = OllamaService()
retriever = RetrievalService()

results = []

for item in questions:
    print(f"Question {item['id']}/10: {item['question']}", flush=True)

    start = time.perf_counter()

    try:
        qvec = ollama.embed(EMBED_MODEL, item["question"])
        retrieved = retriever.search(qvec, 4)

        sources = [x["source"] for x in retrieved]

        matched = any(
            any(expected in source for source in sources)
            for expected in item.get("expected_sources", [])
        )

        results.append({
            "id": item["id"],
            "question": item["question"],
            "expected_sources": item["expected_sources"],
            "retrieved_sources": sources,
            "retrieval_correct": matched,
            "latency_seconds": round(time.perf_counter() - start, 3)
        })

        print(
            f"  Retrieval: {'PASS' if matched else 'FAIL'} | "
            f"Sources: {', '.join(sources)}",
            flush=True
        )

    except Exception as e:
        results.append({
            "id": item["id"],
            "question": item["question"],
            "expected_sources": item["expected_sources"],
            "retrieved_sources": [],
            "retrieval_correct": False,
            "error": str(e),
            "latency_seconds": round(time.perf_counter() - start, 3)
        })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

passed = sum(r["retrieval_correct"] for r in results)
accuracy = (passed / len(results)) * 100 if results else 0
latency = mean(r["latency_seconds"] for r in results) if results else 0

print("\n===== MediCode Retrieval Evaluation =====")
print(f"Questions: {len(results)}")
print(f"Correct retrievals: {passed}/{len(results)}")
print(f"Retrieval Accuracy: {accuracy:.2f}%")
print(f"Average Retrieval Latency: {latency:.2f}s")
print(f"Results saved to: {OUTPUT}")
