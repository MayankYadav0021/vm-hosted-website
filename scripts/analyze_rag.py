import json, os
from app.services.rag_service import RAGService

questions = [
    "Which files are involved in authentication?",
    "What happens after a user submits registration?",
    "Which function calls the payment module?",
    "What does the project documentation say about authentication?",
    "What component does not exist in this project?"
]
rag = RAGService()
rows = []
for q in questions:
    try:
        a = rag.answer(q)
        d = rag.direct_answer(q)
        rows.append({
            "question": q,
            "retrieved_context": [
                {"source": x["source"], "score": x["score"], "text": x["text"]}
                for x in a["retrieved"]
            ],
            "rag_response": a["text"],
            "direct_response": d["text"],
            "rag_latency": a["latency_seconds"],
            "direct_latency": d["latency_seconds"]
        })
    except Exception as e:
        rows.append({"question": q, "error": str(e)})
os.makedirs("results", exist_ok=True)
with open("results/rag_analysis.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2)
print("Saved results/rag_analysis.json")
