# AI-DevOps-Project

## LLM Performance Research Dashboard

An AWS-hosted platform for benchmarking Large Language Models (LLMs), evaluating CPU inference, precision optimization, batching, and LoRA fine-tuning.

## Features
- Multi-model CPU benchmarking
- Inference time, throughput and RAM analysis
- FP32 and FP16 precision comparison
- Batch-size performance analysis
- LoRA fine-tuning
- Interactive HTML, CSS and JavaScript dashboard
- FastAPI backend and experiment history
- Live AWS EC2 resource monitoring

## Technology Stack
Python, FastAPI, PyTorch, Transformers, PEFT, Pandas, NumPy, Matplotlib, HTML, CSS, JavaScript, AWS EC2, Ubuntu and Nginx.

## Project Structure
- app/: Backend and frontend
- phase1_cpu/: Model benchmarking
- phase2_cpu/: Precision and batching
- phase3_lora/: LoRA fine-tuning
- models/: Fine-tuned adapter
- results/: Benchmark outputs
- figures/: Performance charts

## Run Locally
Install dependencies using pip install -r requirements.txt, then run uvicorn app.backend.main:app --host 127.0.0.1 --port 8000.

## AWS Deployment
Deployed on Ubuntu AWS EC2 using FastAPI, systemd and Nginx. Dashboard access is provided through an SSH tunnel.

## Results
Benchmark CSV and JSON files are stored in results/, charts in figures/, and the LoRA adapter in models/phase3_lora/adapter/.
