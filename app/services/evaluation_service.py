import json
import psutil
import time

from app.config import EMBED_MODEL
from app.services.ollama_service import OllamaService
from app.services.retrieval_service import RetrievalService


def keyword_score(text, keywords):
    if not keywords:
        return 0.0

    text_lower = text.lower()

    matched = sum(
        1 for keyword in keywords
        if keyword.lower() in text_lower
    )

    return matched / len(keywords)


def code_test_pass_rate(text, test_cases):
    """
    Simple evaluation for questions that contain executable
    Python test cases.

    Returns:
        1.0 = all tests passed
        0.0 = failed / not executable
        None = no test cases supplied
    """

    if not test_cases:
        return None

    import re
    import subprocess
    import tempfile
    import os

    # Extract Python code block
    match = re.search(
        r"```python\s*(.*?)```",
        text,
        re.DOTALL | re.IGNORECASE
    )

    if not match:
        match = re.search(
            r"```\s*(.*?)```",
            text,
            re.DOTALL
        )

    if not match:
        return 0.0

    generated_code = match.group(1)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8"
    ) as f:

        f.write(generated_code)
        f.write("\n\n")

        for test in test_cases:
            f.write(test + "\n")

        test_file = f.name

    try:
        result = subprocess.run(
            ["python3", test_file],
            capture_output=True,
            text=True,
            timeout=10
        )

        return 1.0 if result.returncode == 0 else 0.0

    except Exception:
        return 0.0

    finally:
        try:
            os.remove(test_file)
        except OSError:
            pass


class EvaluationService:

    def __init__(self):
        self.ollama = OllamaService()
        self.retriever = RetrievalService()

    def evaluate_question(self, model, item):

        start = time.perf_counter()

        process = psutil.Process()
        before = process.memory_info().rss

        try:

            # -----------------------------
            # 1. Create query embedding
            # -----------------------------

            qvec = self.ollama.embed(
                EMBED_MODEL,
                item["question"]
            )

            # -----------------------------
            # 2. Retrieve relevant chunks
            # -----------------------------

            retrieved = self.retriever.search(
                qvec,
                4
            )

            context = "\n\n".join(
                x["text"]
                for x in retrieved
            )

            # -----------------------------
            # 3. Generate LLM response
            # -----------------------------

            prompt = (
                "Use only the supplied context. "
                "Do not invent facts.\n\n"
                "CONTEXT:\n"
                + context
                + "\n\nQUESTION:\n"
                + item["question"]
            )

            result = self.ollama.chat(
                model,
                prompt,
                0.1
            )

            answer = result["text"]

            # -----------------------------
            # 4. Metrics
            # -----------------------------

            sources = [
                x["source"]
                for x in retrieved
            ]

            expected_sources = item.get(
                "expected_sources",
                []
            )

            if expected_sources:

                source_matches = sum(
                    any(
                        expected in source
                        for source in sources
                    )
                    for expected in expected_sources
                )

                retrieval_quality = (
                    source_matches /
                    len(expected_sources)
                )

            else:
                retrieval_quality = 0.0

            relevance = keyword_score(
                answer,
                item.get("expected_keywords", [])
            )

            hallucination_proxy = int(
                bool(item.get("expected_keywords"))
                and relevance == 0
            )

            code_pass_rate = code_test_pass_rate(
                answer,
                item.get("test_cases", [])
            )

            latency = time.perf_counter() - start

            after = process.memory_info().rss

            result_row = {
                "question_id": item["id"],
                "model": model,
                "status": "success",
                "question": item["question"],

                "answer": answer.replace(
                    "\n",
                    " "
                ),

                "retrieved_sources": ";".join(
                    sources
                ),

                "correctness_proxy": round(
                    relevance,
                    3
                ),

                "relevance": round(
                    relevance,
                    3
                ),

                "retrieval_quality": round(
                    retrieval_quality,
                    3
                ),

                "hallucination_flag_proxy":
                    hallucination_proxy,

                "code_test_pass_rate":
                    code_pass_rate,

                "latency_seconds": round(
                    latency,
                    3
                ),

                "prompt_tokens":
                    result.get(
                        "prompt_tokens",
                        0
                    ),

                "output_tokens":
                    result.get(
                        "output_tokens",
                        0
                    ),

                "memory_delta_mb": round(
                    (
                        after - before
                    ) / (1024 ** 2),
                    3
                )
            }

            return result_row

        except Exception as e:

            latency = time.perf_counter() - start

            after = process.memory_info().rss

            return {
                "question_id": item["id"],
                "model": model,
                "status": "failed",
                "question": item["question"],
                "answer": "",
                "error": str(e),
                "retrieved_sources": "",
                "correctness_proxy": 0,
                "relevance": 0,
                "retrieval_quality": 0,
                "hallucination_flag_proxy": 0,
                "code_test_pass_rate": None,
                "latency_seconds": round(
                    latency,
                    3
                ),
                "prompt_tokens": 0,
                "output_tokens": 0,
                "memory_delta_mb": round(
                    (
                        after - before
                    ) / (1024 ** 2),
                    3
                )
            }

    def evaluate(
        self,
        models,
        path="data/evaluation_questions.json"
    ):

        with open(
            path,
            encoding="utf-8"
        ) as f:

            dataset = json.load(f)

        results = []

        for model in models:

            print(
                f"\n===== Evaluating {model} ====="
            )

            for item in dataset:

                print(
                    f"Question {item['id']} "
                    f"with {model}"
                )

                result = self.evaluate_question(
                    model,
                    item
                )

                results.append(result)

                print(
                    f"Status: {result['status']} | "
                    f"Latency: "
                    f"{result['latency_seconds']}s"
                )

        return results
