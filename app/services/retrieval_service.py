import json, os
import numpy as np
from app.config import VECTOR_FILE, META_FILE, TOP_K

def cosine_similarity(query, matrix):
    q = np.asarray(query, dtype=np.float32)
    m = np.asarray(matrix, dtype=np.float32)
    denom = np.maximum(np.linalg.norm(m, axis=1) * max(np.linalg.norm(q), 1e-12), 1e-12)
    return (m @ q) / denom

class RetrievalService:
    def __init__(self):
        self.vectors = None
        self.metadata = []
        self.load()

    def load(self):
        if os.path.exists(VECTOR_FILE) and os.path.exists(META_FILE):
            self.vectors = np.load(VECTOR_FILE)["vectors"]
            with open(META_FILE, encoding="utf-8") as f:
                self.metadata = json.load(f)

    def search(self, query_vector, top_k=TOP_K):
        if self.vectors is None:
            raise RuntimeError("Knowledge base not indexed. Run: python scripts/ingest.py")
        scores = cosine_similarity(query_vector, self.vectors)
        ids = np.argsort(scores)[::-1][:top_k]
        return [{**self.metadata[int(i)], "score": float(scores[int(i)])} for i in ids]
