# CodeBase RAG Assistant — Weeks 1–4

One continuous application for the lab.

## Week 1
`week1_site/index.html` is the static website to host with Apache on the VM. Use Git/GitHub to commit and push updates.

## Week 2
`week2/run_ollama.py` demonstrates sending a prompt to Code Llama through Ollama.

## Week 3
FastAPI + Ollama + Code Llama + knowledge base + chunking + Ollama embeddings + cosine similarity + retrieval + RAG + service separation + Docker.

## Week 4
Three-model evaluation, 25 representative questions, latency/token/memory measurements, retrieval-quality analysis, RAG vs direct comparison, and multi-file/repository-style questions.

## Setup
```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

Start Ollama separately:
```bash
ollama serve
ollama pull codellama:7b
ollama pull starcoder2:3b
ollama pull qwen2.5-coder:3b
ollama pull nomic-embed-text
```

Configure:
```bash
# Windows
copy .env.example .env
# Linux
cp .env.example .env
```

Index:
```bash
python scripts/ingest.py
```

Run API:
```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

Evaluate:
```bash
python scripts/evaluate_models.py
python scripts/analyze_rag.py
```

## Week 4 metric definitions
Correctness/relevance are keyword-based proxies and should be manually validated for the final report. Retrieval quality is the fraction of expected source files found in top-k. Hallucination is a simple zero-keyword flag and must be manually reviewed. Test-pass rate should be measured separately for generated-code questions by running generated tests. Latency is wall-clock time. Token usage comes from Ollama prompt/eval counts. Memory is process RSS delta.

## Presentation
Show `/docs`, a RAG response with retrieved sources, the model comparison CSV, the RAG analysis JSON, and a multi-file question.
