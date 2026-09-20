# Week 4 - LLM Evaluation, RAG Analysis and Codebase Understanding

## 1. Objective

Week 4 continued the same LLM application developed during Week 3.

The objective was to evaluate multiple local code-oriented language models using a common evaluation dataset, measure quality and performance, analyze the RAG pipeline, and test understanding of a multi-file software codebase.

The application used Ollama as the local model runtime and the existing RAG pipeline from Week 3.

## 2. Models Evaluated

The following local models were considered:

1. Qwen 2.5 Coder 3B
2. StarCoder2 3B
3. Code Llama 7B

All models were accessed through Ollama.

The VM used for evaluation was CPU-only with approximately 7.2 GB of RAM.

## 3. Evaluation Dataset

A common dataset of 25 software-project questions was used for the main model evaluation.

The questions covered authentication, API behavior, project architecture, registration, retrieval, documentation, project components, and software development concepts.

Qwen 2.5 Coder 3B and StarCoder2 3B were evaluated against all 25 questions.

Code Llama 7B was evaluated on the first 5 questions because the 7B model required substantially more CPU time on the available VM.

No missing Code Llama results were fabricated.

## 4. Quantitative Evaluation Metrics

### Success Rate

Success Rate = Successful Requests / Attempted Requests × 100

This measures how many model requests completed successfully.

### Correctness Proxy

A keyword-based correctness proxy was used to estimate whether the response contained expected answer information.

This is an automated proxy and should not be treated as human-verified accuracy.

### Relevance

The relevance score used the automated expected-answer matching approach.

### Retrieval Quality

Retrieval quality measured whether expected knowledge-base sources were retrieved.

This does not measure whether the ranking of retrieved documents was optimal.

### Hallucination Flag Proxy

The hallucination metric was implemented as an automated proxy based on expected information.

It is not a human-verified hallucination rate.

### Latency

Latency was measured as the time required to complete each model request.

### Token Usage

Prompt tokens and output tokens were collected from Ollama response metadata when available.

## 5. Model Evaluation Results

### Qwen 2.5 Coder 3B

Questions attempted: 25

Successful: 25

Failed: 0

Success rate: 100%

Average correctness proxy: 0.720

Average relevance: 0.720

Average retrieval quality: 1.000

Average hallucination flag proxy: 0.120

Average latency: 85.36 seconds

Average prompt tokens: 527.72

Average output tokens: 73.80

### StarCoder2 3B

Questions attempted: 25

Successful: 15

Failed: 10

Success rate: 60%

Average correctness proxy: 0.356

Average relevance: 0.356

Average retrieval quality: 1.000

Average hallucination flag proxy: 0.333

Average latency: 78.45 seconds

Average prompt tokens: 583.33

Average output tokens: 27.80

### Code Llama 7B

Questions attempted: 5

Successful: 1

Failed: 4

Success rate: 20%

Average correctness proxy: 0.500

Average relevance: 0.500

Average retrieval quality: 1.000

Average hallucination flag proxy: 0.000

Average latency for successful requests: 170.37 seconds

Average prompt tokens: 617.00

Average output tokens: 24.00

The Code Llama evaluation was stopped after five questions because the 7B model was computationally expensive on the CPU-only VM. The remaining results were intentionally not fabricated.

## 6. Model Comparison

| Metric | Qwen 2.5 Coder 3B | StarCoder2 3B | Code Llama 7B |
|---|---:|---:|---:|
| Questions attempted | 25 | 25 | 5 |
| Successful | 25 | 15 | 1 |
| Failed | 0 | 10 | 4 |
| Success rate | 100% | 60% | 20% |
| Correctness proxy | 0.720 | 0.356 | 0.500 |
| Relevance | 0.720 | 0.356 | 0.500 |
| Retrieval quality | 1.000 | 1.000 | 1.000 |
| Hallucination flag proxy | 0.120 | 0.333 | 0.000 |
| Average latency | 85.36 s | 78.45 s | 170.37 s |
| Average prompt tokens | 527.72 | 583.33 | 617.00 |
| Average output tokens | 73.80 | 27.80 | 24.00 |

Because Code Llama was tested on only five questions, its results are not directly comparable to the two models evaluated on the full 25-question dataset.

The results demonstrate a trade-off between model size, response time, reliability, and response quality on a CPU-constrained virtual machine.

## 7. RAG Pipeline Analysis

The Week 3 RAG implementation followed this pipeline:

QUESTION
↓
QUERY EMBEDDING
↓
VECTOR SIMILARITY SEARCH
↓
TOP-K RELEVANT DOCUMENTS
↓
CONTEXT CONSTRUCTION
↓
LLM
↓
GROUNDED RESPONSE

The embedding model used was:

nomic-embed-text

The RAG system retrieved relevant documentation before sending the context to the language model.

## 8. RAG Example

During Week 3 testing, an authentication question was submitted to the RAG endpoint.

The system retrieved:

- authentication.md
- api.md
- architecture.md
- README.md

The authentication document received the highest similarity score.

The LLM then generated an answer using the retrieved context.

This demonstrated that the application could combine vector retrieval with local LLM generation.

## 9. RAG vs Direct LLM

A direct LLM request does not have access to the application's project-specific knowledge unless that information is already contained in the model's training data or supplied in the prompt.

The RAG implementation adds project-specific context before generation.

Direct LLM:

Question → LLM → Answer

RAG:

Question → Embedding → Retrieval → Context → LLM → Answer

The main benefit of the RAG architecture is that responses can be grounded in the application's knowledge base.

However, incorrect or irrelevant retrieval can reduce response quality.

## 10. Exercise 6 - Repository / Codebase Understanding

A separate multi-file software codebase was created to test repository-level understanding.

The codebase contained authentication, registration, payment, API, and test modules.

Structure:

sample_codebase/
├── auth/
│   ├── auth_service.py
│   └── session.py
├── users/
│   ├── user_service.py
│   └── registration.py
├── payments/
│   └── payment_service.py
├── api/
│   ├── auth_routes.py
│   ├── registration_routes.py
│   └── payment_routes.py
└── tests/
    ├── test_auth.py
    ├── test_registration.py
    └── test_payment.py

Ten repository-understanding questions were created.

The questions covered:

- Authentication files
- Authentication functions
- Session management
- Registration flow
- User creation
- Payment processing
- API-to-payment relationships
- Authentication tests
- Impacted files
- Registration dependencies

The deterministic codebase verification produced:

Total questions: 10

Passed: 10

Failed: 0

Pass rate: 100%

The codebase was also tested using pytest:

3 tests passed.

This 100% result represents deterministic verification of the known codebase structure and should not be interpreted as an LLM accuracy score.

## 10. Exercise 6 - Repository / Codebase Understanding

A separate multi-file software codebase was created to test repository-level understanding.

The codebase contained authentication, registration, payment, API, and test modules.

Structure:

sample_codebase/
├── auth/
│   ├── auth_service.py
│   └── session.py
├── users/
│   ├── user_service.py
│   └── registration.py
├── payments/
│   └── payment_service.py
├── api/
│   ├── auth_routes.py
│   ├── registration_routes.py
│   └── payment_routes.py
└── tests/
    ├── test_auth.py
    ├── test_registration.py
    └── test_payment.py

Ten repository-understanding questions were created.

The questions covered:

- Authentication files
- Authentication functions
- Session management
- Registration flow
- User creation
- Payment processing
- API-to-payment relationships
- Authentication tests
- Impacted files
- Registration dependencies

The deterministic codebase verification produced:

Total questions: 10

Passed: 10

Failed: 0

Pass rate: 100%

The codebase was also tested using pytest:

3 tests passed.

This 100% result represents deterministic verification of the known codebase structure and should not be interpreted as an LLM accuracy score.

## 13. Overall Findings

The Week 4 experiments demonstrated the complete evaluation workflow for the LLM application.

The application was able to:

- Run multiple local code-oriented LLMs
- Send common evaluation questions to the models
- Record latency and token usage
- Measure automated quality proxies
- Perform vector-based retrieval
- Ground LLM responses using retrieved context
- Analyze a multi-file software codebase
- Execute automated tests
- Record evaluation results for later analysis

The experiments also demonstrated that model evaluation must consider both response quality and system resources.

On the available CPU-only VM, model size had a significant effect on inference time and reliability.

The experiment therefore demonstrates the importance of evaluating models under the actual deployment constraints of an application rather than considering model capability alone.

## 14. Conclusion

Week 4 extended the Week 3 LLM application into an evaluation and analysis system.

Multiple local models were tested using a common question set, quantitative measurements were collected, the RAG pipeline was analyzed, and repository-level understanding was demonstrated using a multi-file codebase.

The final implementation provides a reproducible foundation for future evaluation on stronger hardware, larger datasets, human-verified quality labels, and more comprehensive code-generation tests.
