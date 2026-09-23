import json

with open("data/medicode_rag_comparison.json", encoding="utf-8") as f:
    comparisons = json.load(f)

retrieval = {
    "C01": [
        ("medicode/appointment_management.md", 0.6768),
        ("medicode/appointment_management.md", 0.6367),
        ("medicode/appointment_management.md", 0.6102),
        ("medicode/system_architecture.md", 0.5525),
    ],
    "C02": [
        ("medicode/patient_management.md", 0.8028),
        ("medicode/patient_management.md", 0.7845),
        ("medicode/patient_management.md", 0.7739),
        ("medicode/billing_management.md", 0.6946),
    ],
    "C03": [
        ("medicode/security_and_authentication.md", 0.8803),
        ("medicode/patient_management.md", 0.7395),
        ("medicode/system_architecture.md", 0.7283),
        ("medicode/patient_management.md", 0.7065),
    ],
}

report = []

for item in comparisons:
    sources = retrieval[item["id"]]
    expected = item["expected_source"]

    report.append({
        "id": item["id"],
        "question": item["question"],
        "without_rag": {
            "retrieved_context": False,
            "source_count": 0
        },
        "with_rag": {
            "retrieved_context": True,
            "top_k": len(sources),
            "expected_source_retrieved": expected in [x[0] for x in sources],
            "sources": [
                {"source": source, "score": score}
                for source, score in sources
            ]
        }
    })

with open("data/medicode_rag_comparison_results.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print("=== MediCode RAG Comparison ===")
for item in report:
    print(f"\n{item['id']}: {item['question']}")
    print("Without RAG: 0 retrieved sources")
    print(
        "With RAG:",
        item["with_rag"]["top_k"],
        "retrieved sources"
    )
    print(
        "Expected source retrieved:",
        item["with_rag"]["expected_source_retrieved"]
    )

print("\nSaved: data/medicode_rag_comparison_results.json")
