### Fine-Tuning Execution & Parameter Breakdown

The QLoRA fine-tuning loop is executed locally using Apple's MLX framework:

\`\`\`bash
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
\`\`\`

#### Hyperparameter Reference

| Parameter | Configuration | Description |
| :--- | :--- | :--- |
| `python -m mlx_lm.lora` | CLI Module | Executes Apple MLX's native low-rank adaptation training script. |
| `--model` | `Meta-Llama-3.1-8B-*-4bit` | Base 4-bit quantized model weights loaded into unified memory. |
| `--train` | Flag | Sets the module into active training mode (calculating loss and backpropagation). |
| `--data` | `./data` | Directory path containing `train.jsonl` and `valid.jsonl` files. |
| `--batch-size` | `1` | Processes one sequence per gradient update step to minimize VRAM memory spikes. |
| `--num-layers 16 ` | `16` | Number of transformer layers (from the top) to attach trainable LoRA adapters to. |
| `--iters` | `1000` | Total training iterations (equivalent to 1 full epoch over a 1,000-sample dataset). |
| `--learning-rate` | `1e-5` | Optimizer step size calibrated to adapt formatting without catastrophic forgetting. |
| `--save-every` | `250` | Saves an adapter checkpoint every 250 steps to prevent progress loss. |
| `--adapter-path` | `./adapters` | Destination directory where the final `adapters.safetensors` file is exported. |