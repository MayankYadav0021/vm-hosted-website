import json
import time

from app.services.ollama_service import OllamaService
from app.services.retrieval_service import RetrievalService
from app.config import EMBED_MODEL, TOP_K

with open("data/medicode_rag_analysis_tests.json", encoding="utf-8") as f:
    tests = json.load(f)

ollama = OllamaService()
retriever = RetrievalService()

relevant_pass = 0
relevant_total = 0
latencies = []

print("=== MediCode RAG Analysis ===")

for item in tests:
    start = time.perf_counter()

    vec = ollama.embed(EMBED_MODEL, item["question"])
    results = retriever.search(vec, TOP_K)

    latency = time.perf_counter() - start
    latencies.append(latency)

    sources = [x["source"] for x in results]

    print(f"\n{item['id']} | {item['type']}")
    print(f"Question: {item['question']}")
    print(f"Expected source: {item['expected_source']}")

    print("Retrieved:")
    for i, x in enumerate(results, 1):
        print(f"  {i}. {x['source']} | score={x['score']:.4f}")

    print(f"Latency: {latency:.2f}s")

    if item["expected_source"]:
        relevant_total += 1
        passed = item["expected_source"] in sources

        if passed:
            relevant_pass += 1

        print(
            "Expected-source retrieval: "
            + ("PASS" if passed else "FAIL")
        )
    else:
        print(
            "Ground-truth source: NONE "
            "(out-of-scope / insufficient-information case)"
        )
        print(
            "Retrieval result is recorded for qualitative RAG analysis; "
            "no PASS/FAIL accuracy score is assigned."
        )

print("\n=== SUMMARY ===")
print(f"Grounded retrieval cases: {relevant_pass}/{relevant_total}")

if relevant_total:
    print(
        f"Grounded retrieval accuracy: "
        f"{relevant_pass / relevant_total * 100:.1f}%"
    )

print(f"Average retrieval latency: {sum(latencies) / len(latencies):.2f}s")
print(f"Total analysis cases: {len(tests)}")
