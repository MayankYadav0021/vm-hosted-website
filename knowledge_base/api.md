# API Documentation

GET /health returns a simple health response showing whether the API is alive and whether Ollama is reachable.

POST /api/chat sends a question directly to the configured LLM without retrieval.

POST /api/rag sends a question through the RAG pipeline. The application creates a query embedding, retrieves relevant chunks using cosine similarity, and supplies the retrieved context to the LLM.

If Ollama is unavailable, the API returns an error for model-dependent operations.
