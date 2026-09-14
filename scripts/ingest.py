import os, json
import numpy as np
from app.config import KB_DIR, EMBED_MODEL, VECTOR_FILE, META_FILE, CHUNK_SIZE, CHUNK_OVERLAP
from app.services.chunking_service import chunk_text
from app.services.ollama_service import OllamaService

EXTENSIONS = {".md", ".txt", ".py", ".js", ".html", ".css", ".json"}

def main():
    os.makedirs("data", exist_ok=True)
    client = OllamaService()
    if not client.health():
        raise SystemExit("Ollama is not running. Start it with: ollama serve")
    chunks = []
    for root, _, names in os.walk(KB_DIR):
        for name in names:
            if os.path.splitext(name)[1].lower() not in EXTENSIONS:
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8", errors="ignore") as f:
                text = f.read()
            rel = os.path.relpath(path, KB_DIR).replace("\\", "/")
            chunks.extend(chunk_text(text, rel, CHUNK_SIZE, CHUNK_OVERLAP))
    if not chunks:
        raise SystemExit("Knowledge base is empty.")
    vectors = []
    for i, c in enumerate(chunks, 1):
        print(f"Embedding {i}/{len(chunks)}: {c['source']}")
        vectors.append(client.embed(EMBED_MODEL, c["text"]))
    np.savez_compressed(VECTOR_FILE, vectors=np.asarray(vectors, dtype=np.float32))
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
    print(f"Indexed {len(chunks)} chunks.")

if __name__ == "__main__":
    main()
