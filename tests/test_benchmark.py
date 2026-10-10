"""
TEST: Model Benchmark Suite
PURPOSE: The ultimate test for model accuracy. Evaluates your Base model vs your Fine-Tuned model on 150 test queries.
It measures valid syntax % and execution accuracy %, and then generates a comparison chart (benchmark_results.png).
"""
import json
import sqlite3
import re
import matplotlib.pyplot as plt
import numpy as np
from mlx_lm import load, generate

TEST_FILE = "./data/test.jsonl"
MODEL_ID = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
ADAPTER_PATH = "./adapters"
SAMPLE_COUNT = 150

def clean_sql(text):
    text = re.sub(r"```sql|```", "", text).strip()
    return text.split(";")[0] + ";"

def extract_json_sql(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text.split("```json")[1].split("```")[0].strip()
    elif text.startswith("```"):
        text = text.split("```")[1].split("```")[0].strip()
    try:
        data = json.loads(text)
        sql = data.get("sql", "")
        return sql.split(";")[0] + ";" if sql else text
    except json.JSONDecodeError:
        return text.split(";")[0] + ";"

def execute_query(schema_ddl, query):
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    try:
        cur.executescript(schema_ddl)
        cur.execute(query)
        res = cur.fetchall()
        return True, res
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def evaluate(model, tokenizer, eval_data, label, use_json=False):
    valid_syntax = 0
    correct_exec = 0
    print(f"\nEvaluating: {label} ({len(eval_data)} samples)...")
    
    with open("test_execution.log", "a", encoding="utf-8") as log_f:
        log_f.write(f"\n{'='*50}\n🚀 RUNNING: {label} (JSON Mode: {use_json})\n{'='*50}\n")
        
        for i, item in enumerate(eval_data, 1):
            schema_raw = item["messages"][1]["content"]
            ground_truth = item["messages"][2]["content"]
            ddl = schema_raw.split("Question:")[0].replace("Schema:", "").strip()
            
            # Extract question for logging
            question = schema_raw.split("Question:")[1].strip() if "Question:" in schema_raw else "Unknown Question"

            messages = [item["messages"][0], item["messages"][1]]
            
            # Override the prompt if using JSON structured output
            if use_json:
                messages[0] = {
                    "role": "system", 
                    "content": "You are an expert SQL generator. Given a database schema and a natural Language question, write the exact SQL query that answers the question. You MUST output your response as a valid JSON object containing exactly one key called \"sql\" with the query as its value. Do not output any conversational text."
                }

            prompt = tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
            
            # Increase max_tokens slightly to accommodate JSON overhead
            output = generate(model, tokenizer, prompt=prompt, max_tokens=150, verbose=False)
            pred_sql = extract_json_sql(output) if use_json else clean_sql(output)

            gt_ok, gt_res = execute_query(ddl, ground_truth)
            pred_ok, pred_res = execute_query(ddl, pred_sql)
            
            # Log to file
            log_f.write(f"\n--- Question {i} ---\n")
            log_f.write(f"Question: {question}\n")
            log_f.write(f"Expected SQL: {ground_truth}\n")
            log_f.write(f"Model Gen SQL: {pred_sql}\n")

            if pred_ok:
                valid_syntax += 1
                if gt_ok and pred_res == gt_res:
                    correct_exec += 1
                    log_f.write(f"Status: ✅ MATCH (Rows: {len(pred_res) if isinstance(pred_res, list) else 0})\n")
                else:
                    log_f.write(f"Status: ❌ MISMATCH\n  Expected Data: {gt_res}\n  Got Data: {pred_res}\n")
            else:
                log_f.write(f"Status: ❌ SYNTAX ERROR\n  Error message: {pred_res}\n")

    syntax_pct = (valid_syntax / len(eval_data)) * 100
    exec_pct = (correct_exec / len(eval_data)) * 100
    print(f"  > Valid Syntax: {syntax_pct:.1f}%")
    print(f"  > Execution Accuracy: {exec_pct:.1f}%")
    return syntax_pct, exec_pct

def generate_social_chart(base_metrics, ft_metrics):
    categories = ['Valid SQL Syntax', 'Execution Accuracy\n(SQLite Matched)']
    base_scores = list(base_metrics)
    ft_scores = list(ft_metrics)

    x = np.arange(len(categories))
    width = 0.32

    # High-contrast modern styling for social feeds
    fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=300)
    fig.patch.set_facecolor('#0F172A')   # Slate 900 background
    ax.set_facecolor('#1E293B')          # Slate 800 plot area

    rects1 = ax.bar(x - width/2, base_scores, width, label='Base Llama-3.1-8B-Instruct', 
                    color='#64748B', edgecolor='#94A3B8', linewidth=1.2, zorder=3)
    rects2 = ax.bar(x + width/2, ft_scores, width, label='Fine-Tuned (QLoRA / Apple MLX)', 
                    color='#38BDF8', edgecolor='#BAE6FD', linewidth=1.2, zorder=3)

    # Value callouts above bars
    def autolabel(rects, highlight=False):
        for rect in rects:
            height = rect.get_height()
            # Use white for high contrast on dark mode
            color = '#FFFFFF'
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 7), textcoords="offset points",
                        ha='center', va='bottom', fontsize=12, fontweight='bold', color=color)

    autolabel(rects1)
    autolabel(rects2, highlight=True)

    # Titles & axes formatting
    ax.set_title('Text-to-SQL Performance: Zero-Shot Base vs QLoRA Fine-Tuning', 
                 fontsize=14, fontweight='bold', color='#F8FAFC', pad=20)
    ax.set_ylabel('Success Rate (%)', fontsize=11, fontweight='medium', color='#94A3B8')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11, fontweight='medium', color='#F8FAFC')
    ax.set_ylim(0, 125)

    # Gridlines and spines
    ax.yaxis.grid(True, linestyle='--', alpha=0.25, color='#CBD5E1', zorder=0)
    ax.xaxis.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors='#94A3B8', length=0)

    # Legend
    legend = ax.legend(
        frameon=True, 
        facecolor='#1E293B', 
        edgecolor='#334155', 
        fontsize=10, 
        loc='upper left',
        bbox_to_anchor=(0.02, 0.98)
    )
    for text in legend.get_texts():
        text.set_color('#E2E8F0')

    # Subtitle / hardware watermark
    plt.figtext(0.5, -0.02, 'Trained locally on Apple Silicon (M-series, 16GB) | MLX Framework | Dataset: sql-create-context',
                ha='center', fontsize=9, color='#64748B')

    plt.tight_layout()
    chart_filename = 'benchmark_results.png'
    plt.savefig(chart_filename, bbox_inches='tight')
    print(f"\nChart generated successfully: {chart_filename}")

if __name__ == "__main__":
    # Clear log file before starting
    with open("test_execution.log", "w", encoding="utf-8") as f:
        f.write("TEST EXECUTION LOG\n")
        f.write("="*50 + "\n")

    with open(TEST_FILE, "r") as f:
        eval_samples = [json.loads(line) for line in f][:SAMPLE_COUNT]

    # 1. Base Model
    model_base, tokenizer = load(MODEL_ID)
    base_results = evaluate(model_base, tokenizer, eval_samples, "Base Model", use_json=True)

    # 2. Fine-Tuned Model
    model_ft, _ = load(MODEL_ID, adapter_path=ADAPTER_PATH)
    ft_results = evaluate(model_ft, tokenizer, eval_samples, "Fine-Tuned Model", use_json=False)

    # 3. Generate Chart
    generate_social_chart(base_results, ft_results)