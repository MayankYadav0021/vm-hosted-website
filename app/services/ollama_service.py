import requests

from app.config import OLLAMA_BASE_URL


class OllamaService:

    def __init__(self, base_url=OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def health(self):
        try:
            return requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            ).ok
        except requests.RequestException:
            return False

    def chat(self, model, prompt, temperature=0.2):
        r = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": 0,
                "options": {
                    "temperature": temperature,
                    "num_predict": 256,
                    "num_ctx": 2048
                }
            },
            timeout=180
        )

        r.raise_for_status()

        d = r.json()

        return {
            "text": d.get("response", ""),
            "prompt_tokens": int(
                d.get("prompt_eval_count") or 0
            ),
            "output_tokens": int(
                d.get("eval_count") or 0
            )
        }

    def embed(self, model, text):
        r = requests.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": model,
                "prompt": text
            },
            timeout=300
        )

        r.raise_for_status()

        return r.json()["embedding"]
