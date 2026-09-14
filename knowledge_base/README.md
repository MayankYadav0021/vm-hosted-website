# CodeBase RAG Assistant

This project is a software-project question answering assistant. FastAPI exposes the application API. Ollama provides local LLM inference. The default primary code model is configured as Code Llama.

The knowledge base is chunked, embedded locally through Ollama, and searched using cosine similarity. Week 4 evaluates three models using the same questions, prompts, knowledge base, and retrieval settings.

The evaluation records latency, prompt token count, output token count, retrieval quality, correctness/relevance proxies, hallucination flags, and memory delta.
