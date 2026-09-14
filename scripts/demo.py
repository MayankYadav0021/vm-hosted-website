from app.services.rag_service import RAGService

rag = RAGService()
for q in [
    "Which files are involved in authentication?",
    "What happens after a user submits registration?",
    "Which module handles payment processing?",
    "What does the project documentation say about authentication?"
]:
    print("\n" + "="*80)
    print("QUESTION:", q)
    r = rag.answer(q)
    print("\nRETRIEVED:")
    for x in r["retrieved"]:
        print(f"- {x['source']} | score={x['score']:.4f}")
    print("\nANSWER:\n", r["text"])
    print("Latency:", round(r["latency_seconds"], 3), "s")
