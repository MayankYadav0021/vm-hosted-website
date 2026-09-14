import os
from dotenv import load_dotenv
load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
MODEL_PRIMARY = os.getenv("MODEL_PRIMARY", "codellama:7b")
MODEL_2 = os.getenv("MODEL_2", "starcoder2:3b")
MODEL_3 = os.getenv("MODEL_3", "qwen2.5-coder:3b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
TOP_K = int(os.getenv("TOP_K", "4"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
VECTOR_FILE = "data/vectors.npz"
META_FILE = "data/metadata.json"
KB_DIR = "knowledge_base"
