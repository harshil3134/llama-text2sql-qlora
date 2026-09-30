# Local MLX Fine-Tuning for Text-to-SQL

This project demonstrates how to locally fine-tune a LLaMA 3.1 8B Instruct model using Apple's MLX framework (`mlx_lm`). The model is fine-tuned to act as an expert SQL generator that converts natural language questions into SQL queries given a database schema.

## Prerequisites

Ensure you have a Python virtual environment set up and the necessary dependencies installed. 

```bash
source venv/bin/activate
```

## 1. Data Preparation

The `data.py` script automates downloading the `b-mc2/sql-create-context` dataset from HuggingFace and formatting it into a chat structure compatible with conversational models.

Run the data preparation script:

```bash
python data.py
```

This script will:
- Shuffle the dataset.
- Extract a subset of 1,000 training samples and 150 validation samples for a fast local run.
- Format each sample into a standard `system`, `user`, and `assistant` role structure.
- Output the formatted data to `./data/train.jsonl` and `./data/valid.jsonl`.

## 2. Fine-Tuning

We use QLoRA (Quantized Low-Rank Adaptation) via the MLX framework to train the model efficiently on Apple Silicon. 

Execute the following command to start the fine-tuning process:

```bash
python -m mlx_lm.lora \
  --model mlx-community/Meta-Llama-3.1-8B-Instruct-4bit \
  --train \
  --data ./data \
  --batch-size 1 \
  --num-layers 16 \
  --iters 1000 \
  --learning-rate 1e-5 \
  --save-every 250 \
  --adapter-path ./adapters
```

### Hyperparameter Breakdown

| Parameter | Description |
| :--- | :--- |
| `--model` | Base 4-bit quantized model weights loaded into unified memory. |
| `--train` | Sets the module into active training mode. |
| `--data` | Directory containing `train.jsonl` and `valid.jsonl`. |
| `--batch-size 1` | Processes one sequence per step to minimize VRAM memory spikes. |
| `--num-layers 16` | Number of transformer layers (from the top) to attach trainable LoRA adapters to. |
| `--iters 1000` | Total training iterations (equivalent to 1 full epoch over a 1,000-sample dataset). |
| `--learning-rate 1e-5` | Optimizer step size calibrated to adapt formatting without catastrophic forgetting. |
| `--save-every 250` | Saves an adapter checkpoint every 250 steps to prevent progress loss. |
| `--adapter-path` | Destination directory where the final `adapters.safetensors` file is exported. |

## 3. Interactive Web App (Streamlit)

You can test your fine-tuned model interactively using the Streamlit web application. This app allows you to define a custom database schema, ask natural language questions, and instantly execute the generated SQL against an in-memory SQLite database to view the real results.

Run the application:

```bash
streamlit run app.py
```

*Note: If you encounter Out-Of-Memory (OOM) errors, the script automatically manages garbage collection to free up VRAM between interactions. Ensure you do not use `@st.cache_resource` unless you downgrade to `mlx < 0.31.2`, due to MLX thread-local stream constraints.*

## 4. Benchmark & Evaluation
To rigorously benchmark the accuracy of your model, this project includes two automated evaluation pipelines:

1. **`test_model.py` (Validation Split Test):** Tests the model on the remaining 150 samples from the original dataset. It generates a social-media-ready chart (`benchmark_results.png`) comparing the base model (using a highly optimized JSON prompt) vs. your fine-tuned model (using the standard prompt).
2. **`evaluation_suite.py` (Aggressive Custom DBs):** Tests the models on 5 highly complex, custom-built databases (E-Commerce, Hospital, University, Airlines, Banking) using raw execution data matching to test complex multi-table joins.

### Latest Benchmark Results (Zero-Shot)
On the local validation split (150 samples) running on Apple Silicon via MLX:
- **Base Model (Llama-3.1-8B-Instruct):** 82.0% Execution Accuracy (even with JSON structured prompting advantage)
- **Fine-Tuned Adapter (QLoRA):** **95.3% Execution Accuracy** (massive reduction in syntax hallucinations)

Run the evaluation suite:

```bash
python evaluation_suite.py
```

You can add additional schemas and questions to `test_dbs.json` to continually expand your benchmark.

### Note on Zero-Shot Accuracy

If you notice lower accuracy on highly complex, aggressive multi-table queries (e.g., scoring 40-60%), remember that this system is currently evaluating the model in a pure **Zero-Shot** environment. It expects the model to perfectly generate complex SQL on the very first try without any intermediate planning. 

To improve accuracy on difficult queries, you can expand this repository into a multi-step Agentic workflow by implementing:
1. **Schema Pruning (RAG)**: Filtering down the schema to only relevant tables before prompting the model.
2. **Chain of Thought (CoT)**: Forcing the model to write a logical step-by-step plan before outputting the final SQL.
3. **Execution-Correction Loop**: Catching SQL execution errors in a sandbox and feeding the error message back to the LLM so it can self-correct its query.
