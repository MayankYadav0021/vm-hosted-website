import os
import gc
import time
import json
import argparse
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import psutil
import torch

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM


# ============================================================
# AI-DEVOPS PHASE 1
# CPU-BASED MODEL PERFORMANCE EXPERIMENT
# ============================================================

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "figures")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

torch.set_num_threads(2)


# ------------------------------------------------------------
# MODEL PORTFOLIO FROM ORIGINAL NOTEBOOK
# ------------------------------------------------------------

MODEL_PORTFOLIO = {
    "microsoft/DialoGPT-small": {
        "size_category": "tiny",
        "architecture": "causal",
    },
    "distilbert/distilgpt2": {
        "size_category": "tiny",
        "architecture": "causal",
    },
    "microsoft/DialoGPT-medium": {
        "size_category": "small",
        "architecture": "causal",
    },
    "microsoft/DialoGPT-large": {
        "size_category": "small",
        "architecture": "causal",
    },
    "facebook/blenderbot-400M-distill": {
        "size_category": "medium",
        "architecture": "seq2seq",
    },
    "google/pegasus-xsum": {
        "size_category": "medium",
        "architecture": "seq2seq",
    },
}


# ------------------------------------------------------------
# ORIGINAL WORKLOAD STRUCTURE
# ------------------------------------------------------------

WORKLOADS = {
    "chat_conversation": {
        "prompts": [
            "Hello! How are you today?",
            "What is artificial intelligence?",
            "Can you explain machine learning simply?",
            "What are the benefits of automation?",
            "Tell me something interesting about technology.",
        ],
        "max_new_tokens": 40,
        "temperature": 0.7,
    },

    "content_generation": {
        "prompts": [
            "Write a short paragraph about the future of technology.",
            "Create a brief description of artificial intelligence.",
            "Write a short introduction to cloud computing.",
            "Explain why automation is important for businesses.",
        ],
        "max_new_tokens": 50,
        "temperature": 0.8,
    },

    "technical_qa": {
        "prompts": [
            "What is a neural network?",
            "Explain the difference between AI and machine learning.",
            "What is a transformer model?",
            "What is the purpose of a database?",
        ],
        "max_new_tokens": 45,
        "temperature": 0.6,
    },
}


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def ram_gb():
    return psutil.Process(os.getpid()).memory_info().rss / (1024 ** 3)


def available_ram_gb():
    return psutil.virtual_memory().available / (1024 ** 3)


def cleanup():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def count_parameters(model):
    return sum(p.numel() for p in model.parameters())


def estimate_fp32_size_gb(parameters):
    return (parameters * 4) / (1024 ** 3)


def get_model_class(architecture):
    if architecture == "seq2seq":
        return AutoModelForSeq2SeqLM
    return AutoModelForCausalLM


def generate_response(model, tokenizer, prompt, max_new_tokens, temperature):
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=256,
    )

    input_tokens = inputs["input_ids"].shape[1]

    start = time.perf_counter()

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            pad_token_id=tokenizer.pad_token_id,
        )

    elapsed = time.perf_counter() - start

    output_tokens = output.shape[1] - input_tokens

    if output_tokens < 0:
        output_tokens = 0

    generated_text = tokenizer.decode(
        output[0],
        skip_special_tokens=True
    )

    return {
        "inference_time_sec": elapsed,
        "input_tokens": input_tokens,
        "output_tokens": int(output_tokens),
        "tokens_per_sec": (
            output_tokens / elapsed if elapsed > 0 else 0
        ),
        "generated_text": generated_text,
    }


# ------------------------------------------------------------
# BENCHMARK ONE MODEL
# ------------------------------------------------------------

def benchmark_model(model_name):

    info = MODEL_PORTFOLIO[model_name]

    print("\n" + "=" * 70)
    print(f"MODEL: {model_name}")
    print("=" * 70)

    result = {
        "model": model_name,
        "size_category": info["size_category"],
        "architecture": info["architecture"],
        "status": "failed",
        "error": "",
    }

    tokenizer = None
    model = None

    try:

        print(f"Available RAM: {available_ram_gb():.2f} GB")
        print("Loading tokenizer...")

        tokenizer = AutoTokenizer.from_pretrained(model_name)

        if tokenizer.pad_token is None:
            if tokenizer.eos_token is not None:
                tokenizer.pad_token = tokenizer.eos_token
            else:
                tokenizer.add_special_tokens(
                    {"pad_token": "[PAD]"}
                )

        model_class = get_model_class(info["architecture"])

        print("Loading model on CPU...")

        load_start = time.perf_counter()

        model = model_class.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        )

        model.eval()

        load_time = time.perf_counter() - load_start

        parameters = count_parameters(model)
        estimated_size = estimate_fp32_size_gb(parameters)

        print(f"Parameters: {parameters:,}")
        print(f"Estimated FP32 model size: {estimated_size:.2f} GB")
        print(f"Model RAM after loading: {ram_gb():.2f} GB")
        print(f"Model loading time: {load_time:.2f} sec")

        result.update({
            "status": "success",
            "parameters": parameters,
            "parameters_millions": parameters / 1e6,
            "estimated_fp32_size_gb": estimated_size,
            "load_time_sec": load_time,
            "ram_after_load_gb": ram_gb(),
        })

        request_results = []

        # ----------------------------------------------------
        # RUN ALL WORKLOADS
        # ----------------------------------------------------

        for workload_name, workload in WORKLOADS.items():

            print("\n" + "-" * 60)
            print(f"WORKLOAD: {workload_name}")
            print("-" * 60)

            for request_id, prompt in enumerate(
                workload["prompts"], start=1
            ):

                before_ram = ram_gb()

                print(
                    f"Request {request_id}/{len(workload['prompts'])}..."
                )

                try:

                    generation = generate_response(
                        model,
                        tokenizer,
                        prompt,
                        workload["max_new_tokens"],
                        workload["temperature"],
                    )

                    after_ram = ram_gb()

                    row = {
                        "model": model_name,
                        "size_category": info["size_category"],
                        "architecture": info["architecture"],
                        "workload": workload_name,
                        "request_id": request_id,
                        "prompt": prompt,
                        "inference_time_sec": generation[
                            "inference_time_sec"
                        ],
                        "input_tokens": generation["input_tokens"],
                        "output_tokens": generation["output_tokens"],
                        "tokens_per_sec": generation["tokens_per_sec"],
                        "ram_before_inference_gb": before_ram,
                        "ram_after_inference_gb": after_ram,
                        "ram_delta_gb": after_ram - before_ram,
                        "generated_text": generation[
                            "generated_text"
                        ],
                    }

                    request_results.append(row)

                    print(
                        f"  Time: "
                        f"{generation['inference_time_sec']:.3f}s"
                    )

                    print(
                        f"  Output tokens: "
                        f"{generation['output_tokens']}"
                    )

                    print(
                        f"  Throughput: "
                        f"{generation['tokens_per_sec']:.2f} tokens/sec"
                    )

                except Exception as e:

                    print(f"  Request failed: {e}")

                    request_results.append({
                        "model": model_name,
                        "size_category": info["size_category"],
                        "architecture": info["architecture"],
                        "workload": workload_name,
                        "request_id": request_id,
                        "prompt": prompt,
                        "inference_time_sec": np.nan,
                        "input_tokens": np.nan,
                        "output_tokens": np.nan,
                        "tokens_per_sec": np.nan,
                        "ram_before_inference_gb": before_ram,
                        "ram_after_inference_gb": ram_gb(),
                        "ram_delta_gb": np.nan,
                        "generated_text": "",
                    })

        # ----------------------------------------------------
        # MODEL SUMMARY
        # ----------------------------------------------------

        model_df = pd.DataFrame(request_results)

        if not model_df.empty:

            result["total_requests"] = len(model_df)

            result["successful_requests"] = int(
                model_df["inference_time_sec"]
                .notna()
                .sum()
            )

            result["avg_inference_time_sec"] = float(
                model_df["inference_time_sec"].mean()
            )

            result["avg_tokens_per_sec"] = float(
                model_df["tokens_per_sec"].mean()
            )

            result["total_output_tokens"] = int(
                model_df["output_tokens"]
                .fillna(0)
                .sum()
            )

            result["avg_output_tokens"] = float(
                model_df["output_tokens"].mean()
            )

            result["peak_ram_gb"] = float(
                model_df[
                    "ram_after_inference_gb"
                ].max()
            )

            result["avg_ram_delta_gb"] = float(
                model_df[
                    "ram_delta_gb"
                ].mean()
            )

        model_df.to_csv(
            os.path.join(
                RESULTS_DIR,
                f"{model_name.replace('/', '_')}_requests.csv"
            ),
            index=False,
        )

        del model
        del tokenizer
        cleanup()

        print("\nModel unloaded successfully.")

        return result

    except Exception as e:

        result["error"] = str(e)

        print("\nMODEL FAILED")
        print(str(e))

        if model is not None:
            del model

        if tokenizer is not None:
            del tokenizer

        cleanup()

        return result


# ------------------------------------------------------------
# PLOTS
# ------------------------------------------------------------

def create_plots(summary_df):

    successful = summary_df[
        summary_df["status"] == "success"
    ].copy()

    if successful.empty:
        print("No successful models available for plots.")
        return

    # Parameters
    plt.figure(figsize=(10, 6))
    plt.bar(
        successful["model"],
        successful["parameters_millions"]
    )
    plt.xticks(rotation=30, ha="right")
    plt.ylabel("Parameters (Millions)")
    plt.title("Phase 1: Model Parameter Comparison")
    plt.tight_layout()
    plt.savefig(
        os.path.join(
            FIGURES_DIR,
            "phase1_model_parameters.png"
        ),
        dpi=150,
    )
    plt.close()

    # Inference time
    plt.figure(figsize=(10, 6))
    plt.bar(
        successful["model"],
        successful["avg_inference_time_sec"]
    )
    plt.xticks(rotation=30, ha="right")
    plt.ylabel("Average Inference Time (seconds)")
    plt.title("Phase 1: Average Inference Time")
    plt.tight_layout()
    plt.savefig(
        os.path.join(
            FIGURES_DIR,
            "phase1_inference_time.png"
        ),
        dpi=150,
    )
    plt.close()

    # Throughput
    plt.figure(figsize=(10, 6))
    plt.bar(
        successful["model"],
        successful["avg_tokens_per_sec"]
    )
    plt.xticks(rotation=30, ha="right")
    plt.ylabel("Tokens / Second")
    plt.title("Phase 1: Model Throughput")
    plt.tight_layout()
    plt.savefig(
        os.path.join(
            FIGURES_DIR,
            "phase1_throughput.png"
        ),
        dpi=150,
    )
    plt.close()

    # RAM
    plt.figure(figsize=(10, 6))
    plt.bar(
        successful["model"],
        successful["peak_ram_gb"]
    )
    plt.xticks(rotation=30, ha="right")
    plt.ylabel("Peak Process RAM (GB)")
    plt.title("Phase 1: Peak RAM Usage")
    plt.tight_layout()
    plt.savefig(
        os.path.join(
            FIGURES_DIR,
            "phase1_peak_ram.png"
        ),
        dpi=150,
    )
    plt.close()


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--models",
        default="distilbert/distilgpt2",
        help=(
            "Comma-separated model names. "
            "Default runs distilgpt2 first as a smoke test."
        ),
    )

    args = parser.parse_args()

    selected_models = [
        m.strip()
        for m in args.models.split(",")
        if m.strip()
    ]

    print("\n" + "=" * 70)
    print("AI-DEVOPS PHASE 1 CPU EXPERIMENT")
    print("=" * 70)

    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"CPU threads: {torch.get_num_threads()}")
    print(
        f"Available RAM at start: "
        f"{available_ram_gb():.2f} GB"
    )

    all_results = []

    for model_name in selected_models:

        if model_name not in MODEL_PORTFOLIO:
            print(
                f"\nSkipping unknown model: {model_name}"
            )
            continue

        result = benchmark_model(model_name)

        all_results.append(result)

    summary_df = pd.DataFrame(all_results)

    summary_path = os.path.join(
        RESULTS_DIR,
        "phase1_model_summary.csv"
    )

    summary_df.to_csv(
        summary_path,
        index=False,
    )

    json_path = os.path.join(
        RESULTS_DIR,
        "phase1_model_summary.json"
    )

    with open(json_path, "w") as f:
        json.dump(
            all_results,
            f,
            indent=2,
            default=str,
        )

    create_plots(summary_df)

    print("\n" + "=" * 70)
    print("PHASE 1 COMPLETE")
    print("=" * 70)

    print("\nSummary:")
    print(summary_df.to_string(index=False))

    print("\nSaved results:")
    print(summary_path)
    print(json_path)
    print(FIGURES_DIR)


if __name__ == "__main__":
    main()

