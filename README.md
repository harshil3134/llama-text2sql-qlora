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
