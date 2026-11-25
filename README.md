# AI-DevOps Project
## LLM Performance Research and Benchmarking Dashboard

An AWS-hosted research platform for benchmarking Large Language Models (LLMs) on CPU infrastructure. It evaluates inference performance, memory usage, precision optimization, batching, and parameter-efficient fine-tuning through an interactive web dashboard.

## Live Academic Demo

http://35.154.206.124/

Deployed on AWS EC2 using Ubuntu, FastAPI, systemd, and Nginx. The demo currently uses HTTP and restricts public experiment execution. It is intended for academic demonstration, not production use.

## Features

- Multi-model CPU benchmarking
- Inference latency, throughput, parameter count, and RAM analysis
- FP32 and FP16 precision comparison
- Batch-size performance benchmarking
- LoRA fine-tuning using PEFT
- Interactive HTML, CSS, and JavaScript dashboard
- FastAPI backend and experiment history
- Live EC2 resource monitoring
- Groq-powered AI model advisor

## Technology Stack

Python, FastAPI, Uvicorn, PyTorch, Hugging Face Transformers, PEFT, NumPy, Pandas, Matplotlib, HTML, CSS, JavaScript, Groq API, AWS EC2, Ubuntu, and Nginx.

## Project Structure

- `app/backend/` — FastAPI application, experiment runner, and model advisor
- `app/frontend/` — Dashboard interface, styling, and JavaScript
- `phase1_cpu/` — Model benchmarking
- `phase2_cpu/` — Precision and batching experiments
- `phase3_lora/` — LoRA fine-tuning
- `models/` — Fine-tuned adapter files
- `results/` — Benchmark outputs, experiment history, and detailed records
- `figures/` — Performance charts
- `requirements.txt` — Python dependencies
- `.env.example` — Environment variable template

## Experimental Results

### Phase 1: Model Benchmarking

Each model was tested with 13 requests.

| Model | Success | Avg. inference | Throughput | Peak RAM |
|---|---:|---:|---:|---:|
| DistilGPT-2 | 13/13 | 1.105 s | 32.50 tokens/s | 1.175 GB |
| DialoGPT-small | 13/13 | 0.274 s | 15.14 tokens/s | 1.310 GB |

Output lengths differed between the models, so these measurements should not be treated as a universal speed ranking.

### Phase 2: Precision Optimization

Three prompts were tested for each precision.

| Metric | FP32 | FP16 |
|---|---:|---:|
| Avg. inference | 0.466 s | 0.449 s |
| Throughput | 34.35 tokens/s | 35.86 tokens/s |
| Peak process RAM | 1.149 GB | 1.012 GB |
| Success | 3/3 | 3/3 |

These are preliminary results from a small workload.

### Phase 2: Batching Optimization

Eight prompts were tested at each batch size.

| Batch size | Throughput | Avg. batch latency |
|---:|---:|---:|
| 1 | 33.54 tokens/s | 0.357 s |
| 2 | 39.11 tokens/s | 0.613 s |
| 4 | 60.96 tokens/s | 0.786 s |
| 8 | 97.93 tokens/s | 0.979 s |

Batch size 8 achieved approximately 2.92 times the throughput of batch size 1 in this experiment. The workload was limited to eight prompts.

### Phase 3: LoRA Fine-Tuning

- Base model: DistilGPT-2
- Training examples: 8
- Epochs: 2
- Trainable parameters: 73,728 (approximately 0.0899%)
- Training loss: 4.1212 to 4.0380
- Training time: approximately 6.10 seconds

The adapter was saved in `models/phase3_lora/adapter/`. A controlled baseline-versus-adapter language-quality evaluation has not been completed, so improved text quality is not claimed.

## Run Locally

Use Python 3.12 or a compatible environment.

1. Clone the repository:

   `git clone https://github.com/MayankYadav0021/vm-hosted-website.git`

2. Enter the project directory:

   `cd vm-hosted-website`

3. Create and activate a virtual environment:

   `python -m venv .venv`

   Windows: `.venv\Scripts\Activate.ps1`

   Linux: `source .venv/bin/activate`

4. Install dependencies:

   `pip install -r requirements.txt`

5. Copy `.env.example` to `.env` and configure your own credentials:

   - `GROQ_API_KEY`
   - `EXPERIMENT_API_TOKEN`

6. Start the application:

   `uvicorn app.backend.main:app --host 127.0.0.1 --port 8000`

7. Open `http://127.0.0.1:8000/`.

Some experiments require model downloads and sufficient system memory. The AI advisor requires a valid Groq API key.

## AWS Deployment

The application runs on Ubuntu EC2. FastAPI is managed through systemd and served through Nginx. Experiment submission is protected by an API token; the public demo does not permit unauthenticated experiment execution.

## Limitations

- Experiments were conducted on CPU infrastructure, not GPU.
- Workloads were small and results depend on hardware and input data.
- Precision and batching findings are preliminary.
- LoRA output quality has not been validated against a controlled baseline.
- The academic demo uses HTTP rather than HTTPS.

## Author

Mayank Yadav
Computer Science and Engineering
BML Munjal University

GitHub: https://github.com/MayankYadav0021
