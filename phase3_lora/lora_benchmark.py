import csv
import json
import os
import platform
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import psutil
import torch
from peft import LoraConfig, TaskType, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = Path(os.environ.get("AI_DEVOPS_RESULTS_DIR", str(ROOT / "results" / "phase3")))
ADAPTER_DIR = Path(os.environ.get("AI_DEVOPS_ADAPTER_DIR", str(ROOT / "models" / "phase3_lora" / "adapter")))
CSV_PATH = RESULTS_DIR / "lora_results.csv"
JSON_PATH = RESULTS_DIR / "lora_results.json"

MODEL_NAME = "distilbert/distilgpt2"
MAX_LENGTH = 96
EPOCHS = 2
LEARNING_RATE = 2e-4

TRAINING_EXAMPLES = [
    ("What is AI?", "AI is technology that enables computers to perform tasks requiring human intelligence."),
    ("What is machine learning?", "Machine learning allows computers to learn patterns from data."),
    ("What is cloud computing?", "Cloud computing provides computing resources and services over the internet."),
    ("What is DevOps?", "DevOps combines software development and IT operations to improve delivery."),
    ("What is model optimization?", "Model optimization improves speed, memory usage, or resource efficiency."),
    ("What is LoRA?", "LoRA fine-tunes a model efficiently by training small low-rank adapter matrices."),
    ("What is inference latency?", "Inference latency is the time a model takes to produce a response."),
    ("What is batching?", "Batching processes multiple inputs together to improve hardware utilization."),
]

EVALUATION_PROMPTS = [
    "What is AI?",
    "What is LoRA?",
    "What is cloud computing?",
]

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ADAPTER_DIR.parent.mkdir(parents=True, exist_ok=True)

    process = psutil.Process(os.getpid())
    start_time = time.perf_counter()
    initial_ram = process.memory_info().rss / (1024 ** 3)

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": MODEL_NAME,
        "device": "cpu",
        "method": "LoRA",
        "status": "running",
        "error": "",
        "epochs": EPOCHS,
        "learning_rate": LEARNING_RATE,
        "training_examples": len(TRAINING_EXAMPLES),
        "evaluation_prompts": len(EVALUATION_PROMPTS),
        "adapter_rank": 4,
        "adapter_alpha": 8,
        "trainable_parameters": "",
        "total_parameters": "",
        "trainable_parameter_percent": "",
        "training_time_sec": "",
        "evaluation_time_sec": "",
        "avg_generation_time_sec": "",
        "peak_process_ram_gb": "",
        "initial_process_ram_gb": round(initial_ram, 4),
        "adapter_path": str(ADAPTER_DIR.relative_to(ROOT)),
        "evaluation_outputs": [],
    }

    try:
        available_gib = psutil.virtual_memory().available / (1024 ** 3)
        print(f"Available system RAM before training: {available_gib:.2f} GiB", flush=True)

        if available_gib < 1.5:
            raise RuntimeError(
                f"Only {available_gib:.2f} GiB RAM is available; "
                "LoRA training requires at least 1.5 GiB available RAM."
            )

        torch.manual_seed(42)
        torch.set_num_threads(max(1, min(2, os.cpu_count() or 1)))

        print(f"Loading tokenizer: {MODEL_NAME}", flush=True)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"

        print("Loading base model on CPU...", flush=True)
        model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
        model.config.pad_token_id = tokenizer.pad_token_id
        model.config.use_cache = False

        config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=4,
            lora_alpha=8,
            lora_dropout=0.05,
            target_modules=["c_attn"],
            bias="none",
        )
        model = get_peft_model(model, config)
        model.train()

        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in model.parameters())

        result["trainable_parameters"] = trainable
        result["total_parameters"] = total
        result["trainable_parameter_percent"] = round(100 * trainable / total, 4)

        optimizer = torch.optim.AdamW(
            [p for p in model.parameters() if p.requires_grad],
            lr=LEARNING_RATE,
        )

        examples = []
        for question, answer in TRAINING_EXAMPLES:
            text = f"Question: {question}\nAnswer: {answer}{tokenizer.eos_token}"
            encoded = tokenizer(
                text,
                truncation=True,
                max_length=MAX_LENGTH,
                padding="max_length",
                return_tensors="pt",
            )
            labels = encoded["input_ids"].clone()
            labels[encoded["attention_mask"] == 0] = -100
            examples.append((encoded["input_ids"], encoded["attention_mask"], labels))

        print(
            f"Training LoRA: {len(examples)} examples, {EPOCHS} epochs, "
            f"{trainable:,} trainable parameters",
            flush=True,
        )
        training_start = time.perf_counter()
        model.train()

        for epoch in range(EPOCHS):
            total_loss = 0.0
            for input_ids, attention_mask, labels in examples:
                optimizer.zero_grad(set_to_none=True)
                output = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )
                loss = output.loss
                loss.backward()
                optimizer.step()
                total_loss += float(loss.detach())

            print(
                f"Epoch {epoch + 1}/{EPOCHS} - "
                f"mean training loss: {total_loss / len(examples):.4f}",
                flush=True,
            )

        result["training_time_sec"] = round(time.perf_counter() - training_start, 3)

        print("Saving trained LoRA adapter...", flush=True)
        model.save_pretrained(ADAPTER_DIR)
        tokenizer.save_pretrained(ADAPTER_DIR)

        print("Evaluating generation latency...", flush=True)
        model.eval()
        model.config.use_cache = True
        outputs = []
        generation_times = []
        evaluation_start = time.perf_counter()

        for prompt in EVALUATION_PROMPTS:
            inputs = tokenizer(f"Question: {prompt}\nAnswer:", return_tensors="pt")
            begin = time.perf_counter()
            with torch.no_grad():
                generated = model.generate(
                    **inputs,
                    max_new_tokens=24,
                    do_sample=False,
                    pad_token_id=tokenizer.pad_token_id,
                )
            elapsed = time.perf_counter() - begin
            generation_times.append(elapsed)

            text = tokenizer.decode(
                generated[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            ).strip()

            outputs.append({
                "prompt": prompt,
                "generated_text": text,
                "generation_time_sec": round(elapsed, 4),
            })

        result["evaluation_time_sec"] = round(
            time.perf_counter() - evaluation_start, 3
        )
        result["avg_generation_time_sec"] = round(
            sum(generation_times) / len(generation_times), 4
        )
        result["evaluation_outputs"] = outputs
        result["status"] = "success"

    except Exception as exc:
        result["status"] = "failed"
        result["error"] = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()

    finally:
        result["total_runtime_sec"] = round(time.perf_counter() - start_time, 3)
        result["peak_process_ram_gb"] = round(
            process.memory_info().rss / (1024 ** 3), 4
        )
        result["python_version"] = platform.python_version()
        result["torch_version"] = torch.__version__

        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        columns = [
            "timestamp", "model", "device", "method", "status", "error",
            "epochs", "learning_rate", "training_examples", "evaluation_prompts",
            "adapter_rank", "adapter_alpha", "trainable_parameters",
            "total_parameters", "trainable_parameter_percent",
            "training_time_sec", "evaluation_time_sec",
            "avg_generation_time_sec", "peak_process_ram_gb",
            "initial_process_ram_gb", "total_runtime_sec", "adapter_path",
        ]
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerow({key: result.get(key, "") for key in columns})

        print("\n===== PHASE 3 RESULT =====", flush=True)
        print("Status:", result["status"], flush=True)
        print("Training time (seconds):", result["training_time_sec"], flush=True)
        print("Trainable parameters:", result["trainable_parameters"], flush=True)
        print("Trainable parameter (%):", result["trainable_parameter_percent"], flush=True)
        print("Average generation time (seconds):", result["avg_generation_time_sec"], flush=True)
        print("Peak process RAM (GiB):", result["peak_process_ram_gb"], flush=True)
        print("CSV:", CSV_PATH, flush=True)
        print("JSON:", JSON_PATH, flush=True)

        if result["status"] != "success":
            raise SystemExit(1)

if __name__ == "__main__":
    main()
