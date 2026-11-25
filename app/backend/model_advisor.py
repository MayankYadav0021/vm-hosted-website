import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GROQ_MODEL = "openai/gpt-oss-20b"

MODEL_CATALOG = {
    "distilbert/distilgpt2": {
        "name": "DistilGPT-2",
        "type": "text generation",
        "strengths": ["lightweight", "fast inference", "CPU experimentation"],
        "best_for": ["basic text generation", "prototyping"],
        "limitations": ["not instruction tuned", "limited conversational ability"],
        "size": "82M parameters",
    },
    "microsoft/DialoGPT-small": {
        "name": "DialoGPT-small",
        "type": "conversational",
        "strengths": ["dialogue", "conversational responses", "small model"],
        "best_for": ["simple chatbots", "basic conversations"],
        "limitations": ["older model", "limited general instruction following"],
        "size": "117M parameters",
    },
    "Qwen/Qwen2.5-0.5B-Instruct": {
        "name": "Qwen2.5 0.5B Instruct",
        "type": "instruction-following",
        "strengths": ["general assistance", "instruction following", "small footprint"],
        "best_for": ["lightweight assistants", "simple question answering"],
        "limitations": ["limited complex reasoning"],
        "size": "0.5B parameters",
    },
    "Qwen/Qwen2.5-Coder-0.5B-Instruct": {
        "name": "Qwen2.5-Coder 0.5B",
        "type": "coding",
        "strengths": ["code generation", "code completion", "programming assistance"],
        "best_for": ["coding assistants", "small development tools"],
        "limitations": ["small model; complex coding tasks may exceed its capability"],
        "size": "0.5B parameters",
    },
    "meta-llama/Llama-3.2-1B-Instruct": {
        "name": "Llama 3.2 1B Instruct",
        "type": "instruction-following",
        "strengths": ["general assistance", "summarization", "instruction following"],
        "best_for": ["lightweight assistants", "summarization", "simple chat"],
        "limitations": ["limited complex reasoning"],
        "size": "1B parameters",
    },
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0": {
        "name": "TinyLlama 1.1B Chat",
        "type": "conversational",
        "strengths": ["chat", "small-scale dialogue", "lightweight deployment"],
        "best_for": ["experimental chatbots", "CPU model research"],
        "limitations": ["lower capability than larger modern instruction models"],
        "size": "1.1B parameters",
    },
}


def read_benchmarks():
    path = ROOT / "results" / "phase1_model_comparison.csv"
    if not path.is_file():
        return []

    results = []
    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row.get("status") != "success":
                continue
            model_id = row.get("model")
            if model_id not in MODEL_CATALOG:
                continue
            try:
                results.append({
                    "model": model_id,
                    "name": MODEL_CATALOG[model_id]["name"],
                    "latency": float(row["avg_inference_time_sec"]),
                    "throughput": float(row["avg_tokens_per_sec"]),
                    "memory": float(row["peak_ram_gb"]),
                    "requests": int(row["successful_requests"]),
                    "total_requests": int(row["total_requests"]),
                    "benchmark_status": "Benchmark complete",
                })
            except (KeyError, ValueError, TypeError):
                continue
    return results


def _fallback_order(query, candidates):
    """Capability-based fallback if the Groq API is unavailable."""
    q = query.lower()
    terms = {
        "coding": ["code", "coding", "programming", "developer", "debug"],
        "conversation": ["chat", "chatbot", "conversation", "customer support"],
        "general": ["assistant", "question", "answer", "general", "summar"],
        "generation": ["write", "generate", "content", "text"],
    }

    task = next(
        (key for key, words in terms.items() if any(w in q for w in words)),
        "general",
    )

    scores = []
    for model_id, profile in candidates.items():
        score = 0
        if task == "coding" and profile["type"] == "coding":
            score += 10
        if task == "conversation" and profile["type"] == "conversational":
            score += 8
        if task == "general" and profile["type"] == "instruction-following":
            score += 8
        if task == "generation" and model_id == "distilbert/distilgpt2":
            score += 5
        if "lightweight" in q or "low ram" in q or "limited memory" in q:
            if "small" in profile["size"] or "82M" in profile["size"]:
                score += 2
        scores.append((score, model_id))

    return [model_id for _, model_id in sorted(scores, reverse=True)]


def _groq_recommend(query, candidates, benchmarks):
    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    benchmark_map = {item["model"]: item for item in benchmarks}

    candidate_data = []
    for model_id, profile in candidates.items():
        candidate_data.append({
            "model_id": model_id,
            **profile,
            "benchmark": benchmark_map.get(model_id, {
                "benchmark_status": "Not yet benchmarked on this EC2 instance"
            }),
        })

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert machine learning model selection advisor. "
                    "Understand the user's actual application, task, quality needs, "
                    "deployment environment and constraints. Select the three most "
                    "suitable candidates from the supplied catalogue. Prioritize task "
                    "capability over raw speed. Never invent benchmark measurements. "
                    "Use only supplied model IDs. Return valid JSON with this shape: "
                    '{"summary":"short explanation","recommendations":['
                    '{"model":"exact model ID","reason":"specific reason for fit"}]}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Application requirements:\n{query}\n\n"
                    f"Available model catalogue and measured benchmark data:\n"
                    f"{json.dumps(candidate_data)}"
                ),
            },
        ],
        response_format={"type": "json_object"},
        max_completion_tokens=900,
        temperature=0.2,
    )

    content = response.choices[0].message.content
    parsed = json.loads(content)
    valid_ids = set(candidates)
    selected = []

    for item in parsed.get("recommendations", []):
        model_id = item.get("model")
        if model_id in valid_ids and model_id not in selected:
            selected.append(model_id)

    if not selected:
        raise ValueError("Groq did not return valid model selections.")

    reason_map = {
        item["model"]: item.get("reason", "")
        for item in parsed.get("recommendations", [])
        if item.get("model") in valid_ids
    }
    return selected[:3], parsed.get("summary", ""), reason_map


def recommend_models(query: str):
    query = query.strip()

    if len(query) < 5:
        raise ValueError("Please describe your application in more detail.")

    benchmarks = read_benchmarks()
    benchmark_map = {item["model"]: item for item in benchmarks}

    reason_map = {}

    try:
        selected, summary, reason_map = _groq_recommend(
            query, MODEL_CATALOG, benchmarks
        )
        engine = "Groq AI"

    except Exception as exc:
        print(f"Groq advisor fallback: {type(exc).__name__}: {exc}")

        selected = _fallback_order(query, MODEL_CATALOG)[:3]
        summary = (
            "Recommendations are based on model capability profiles. "
            "The AI reasoning service was unavailable for this request."
        )
        engine = "Capability-based fallback"
        reason_map = {}

    for model_id in _fallback_order(query, MODEL_CATALOG):
        if len(selected) >= 3:
            break
        if model_id not in selected:
            selected.append(model_id)

    recommendations = []

    for model_id in selected:
        profile = MODEL_CATALOG[model_id]
        measured = benchmark_map.get(model_id)

        reasons = (
            [reason_map[model_id]]
            if reason_map.get(model_id)
            else [
                profile["strengths"][0],
                profile["best_for"][0],
            ]
        )

        recommendations.append({
            "model": model_id,
            "name": profile["name"],
            "type": profile["type"],
            "size": profile["size"],
            "reasons": reasons,
            "benchmark_status": (
                "Benchmark complete"
                if measured
                else "Not yet benchmarked on this EC2 instance"
            ),
            "latency": measured["latency"] if measured else None,
            "throughput": measured["throughput"] if measured else None,
            "memory": measured["memory"] if measured else None,
            "requests": measured["requests"] if measured else None,
            "total_requests": (
                measured["total_requests"] if measured else None
            ),
        })

    return {
        "query": query,
        "summary": summary,
        "engine": engine,
        "recommendations": recommendations,
        "benchmark_count": len(benchmarks),
        "limitations": [
            "Unbenchmarked models have no measured latency, throughput or RAM values.",
            "Model capability descriptions are catalogue information, not quality-test results.",
            "Actual performance depends on hardware, model configuration and workload.",
        ],
    }
