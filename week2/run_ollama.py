import requests

model = "codellama:7b"
r = requests.post(
    "http://127.0.0.1:11434/api/generate",
    json={"model": model,
          "prompt": "Write a Python function to check whether a number is prime.",
          "stream": False},
    timeout=600
)
r.raise_for_status()
print(r.json().get("response", ""))
