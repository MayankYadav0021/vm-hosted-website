# Architecture

The request flow is:
User -> FastAPI -> RAG Service -> Retrieval Service -> Ollama embeddings -> cosine similarity -> relevant chunks -> Ollama LLM -> response.

The RetrievalService loads vectors from data/vectors.npz and metadata from data/metadata.json. It computes cosine similarity between a query embedding and all stored chunk embeddings, then returns the top-k chunks.

The RAGService creates the query embedding, retrieves context, builds a grounded prompt, and calls the Ollama service.

The OllamaService communicates with the local Ollama HTTP API. It provides chat generation and embedding operations.

The application is orchestrated by FastAPI. The major logical services are application/API service, retrieval service, embedding/LLM service, and knowledge-base data service.

If retrieval returns poor context, the final answer can also be poor. RAG is not a guarantee against hallucination.
