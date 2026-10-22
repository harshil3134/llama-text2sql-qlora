"""
TEST: DML Adapter Benchmark Suite
PURPOSE: Evaluate the fine-tuned DML QLoRA adapter against the base Llama 3.1 8B
         on 100 held-out validation samples. Measures:
           - Valid DML Syntax %      (generated SQL is parseable DML)
           - Safe Execution %        (runs on SQLite in-memory without crashing)
           - WHERE Clause Safety %   (no unbounded UPDATE/DELETE slips through)
           - DML Type Distribution   (INSERT / UPDATE / DELETE breakdown)
         Saves a comparison chart to: dml_benchmark_results.png
"""

import json
import re
import sqlite3
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import sqlglot
from sqlglot import exp
from mlx_lm import load, generate

# ─── Configuration ────────────────────────────────────────────────────────────
VALID_FILE   = "./data_dml/valid.jsonl"
MODEL_ID     = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
ADAPTER_PATH = "./adapters_dml"
SAMPLE_COUNT = 100          # Use first 100 of 140 validation samples
MAX_TOKENS   = 200          # DML can be verbose (INSERTs with many columns)
LOG_FILE     = "dml_test_execution.log"
CHART_FILE   = "dml_benchmark_results.png"
# ──────────────────────────────────────────────────────────────────────────────


def clean_output(text: str) -> str:
    """Strip markdown fences and extract first DML statement."""
    text = re.sub(r"```sql|```", "", text).strip()
    match = re.search(r"(INSERT|UPDATE|DELETE).*?;", text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(0).strip()
    return text.strip().split(";")[0] + ";"


def classify_dml(sql: str) -> str:
    """Return the DML type: INSERT / UPDATE / DELETE / UNKNOWN."""
    s = sql.strip().upper()
    if s.startswith("INSERT"):
        return "INSERT"
    elif s.startswith("UPDATE"):
        return "UPDATE"
    elif s.startswith("DELETE"):
        return "DELETE"
    return "UNKNOWN"


def is_valid_dml(sql: str) -> bool:
    """AST check: must be INSERT, UPDATE, or DELETE."""
    try:
        parsed = sqlglot.parse_one(sql, read="sqlite")
        return isinstance(parsed, (exp.Insert, exp.Update, exp.Delete))
    except Exception:
        return False


def has_where_clause(sql: str) -> bool:
    """True if an UPDATE/DELETE has an explicit WHERE clause."""
    try:
        parsed = sqlglot.parse_one(sql, read="sqlite")
        if isinstance(parsed, (exp.Update, exp.Delete)):
            return bool(parsed.find(exp.Where))
        return True  # INSERT doesn't need WHERE
    except Exception:
        return False


def safe_execute(schema_ddl: str, dml_sql: str) -> tuple:
    """
    Run DML inside a rolled-back transaction on an in-memory SQLite DB.
    Returns (success: bool, error_message: str).
    """
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    try:
        cur.executescript(schema_ddl)
        conn.execute("BEGIN")
        cur.execute(dml_sql)
        conn.rollback()
        return True, ""
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def evaluate(model, tokenizer, samples, label, log_f):
    """
    Run evaluation on samples list.
    Returns dict of metric scores and per-type counts.
    """
    total = len(samples)
    valid_dml   = 0
    safe_exec   = 0
    where_safe  = 0
    update_delete_count = 0

    type_counts = {"INSERT": 0, "UPDATE": 0, "DELETE": 0, "UNKNOWN": 0}

    log_f.write(f"\n{'='*60}\n EVALUATING: {label}  ({total} samples)\n{'='*60}\n")
    print(f"\n── Evaluating: {label} ({total} samples) ──")

    for i, item in enumerate(samples, 1):
        msgs = item["messages"]
        schema_raw   = msgs[1]["content"]
        ground_truth = msgs[2]["content"]

        ddl      = schema_raw.split("Question:")[0].replace("Schema:", "").strip()
        question = schema_raw.split("Question:")[-1].strip()

        prompt = tokenizer.apply_chat_template(
            [msgs[0], msgs[1]],
            tokenize=False,
            add_generation_prompt=True
        )

        raw_output = generate(model, tokenizer, prompt=prompt,
                              max_tokens=MAX_TOKENS, verbose=False)
        pred_sql = clean_output(raw_output)
        dml_type = classify_dml(pred_sql)
        type_counts[dml_type] += 1

        is_dml  = is_valid_dml(pred_sql)
        ok_exec, err = safe_execute(ddl, pred_sql) if is_dml else (False, "Not valid DML")
        where_ok = has_where_clause(pred_sql)

        if is_dml:
            valid_dml += 1
        if ok_exec:
            safe_exec += 1
        if dml_type in ("UPDATE", "DELETE"):
            update_delete_count += 1
            if where_ok:
                where_safe += 1

        status = "OK" if ok_exec else "FAIL"
        log_f.write(
            f"\n[{i:03d}] {status} {dml_type}\n"
            f"  Q:  {question[:120]}\n"
            f"  GT: {ground_truth}\n"
            f"  ->  {pred_sql}\n"
            + (f"  ERR: {err}\n" if err else "")
        )

        if i % 10 == 0:
            print(f"  [{i}/{total}] valid_dml={valid_dml}  safe_exec={safe_exec}", flush=True)

    syntax_pct = (valid_dml / total) * 100
    exec_pct   = (safe_exec / total) * 100
    where_pct  = (where_safe / update_delete_count * 100) if update_delete_count else 100.0

    print(f"\n  Results for {label}:")
    print(f"    Valid DML Syntax  : {syntax_pct:.1f}%  ({valid_dml}/{total})")
    print(f"    Safe Execution    : {exec_pct:.1f}%  ({safe_exec}/{total})")
    print(f"    WHERE Clause Safe : {where_pct:.1f}%  ({where_safe}/{update_delete_count} UPDATE/DELETE)")
    print(f"    DML Breakdown     : {type_counts}")

    log_f.write(
        f"\n-- SUMMARY: {label} --\n"
        f"  Valid DML Syntax : {syntax_pct:.1f}%\n"
        f"  Safe Execution   : {exec_pct:.1f}%\n"
        f"  WHERE Safe       : {where_pct:.1f}%\n"
        f"  Type Breakdown   : {type_counts}\n"
    )

    return {
        "label":  label,
        "syntax": syntax_pct,
        "exec":   exec_pct,
        "where":  where_pct,
        "types":  type_counts,
    }


def generate_chart(base, ft):
    """Render a dark-mode 3-metric comparison bar chart."""
    metrics   = ["Valid DML\nSyntax %", "Safe\nExecution %", "WHERE Clause\nSafety %"]
    base_vals = [base["syntax"], base["exec"], base["where"]]
    ft_vals   = [ft["syntax"],   ft["exec"],   ft["where"]]

    x     = np.arange(len(metrics))
    width = 0.30

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    fig.patch.set_facecolor("#0F172A")
    ax.set_facecolor("#1E293B")

    bars_base = ax.bar(x - width / 2, base_vals, width,
                       label="Base Llama-3.1-8B-Instruct",
                       color="#64748B", edgecolor="#94A3B8", linewidth=1.1, zorder=3)
    bars_ft   = ax.bar(x + width / 2, ft_vals, width,
                       label="DML Fine-Tuned (QLoRA / Apple MLX)",
                       color="#34D399", edgecolor="#6EE7B7", linewidth=1.1, zorder=3)

    for bars in (bars_base, bars_ft):
        for rect in bars:
            h = rect.get_height()
            ax.annotate(f"{h:.1f}%",
                        xy=(rect.get_x() + rect.get_width() / 2, h),
                        xytext=(0, 6), textcoords="offset points",
                        ha="center", va="bottom",
                        fontsize=11, fontweight="bold", color="#FFFFFF")

    ax.set_title("DML Adapter Benchmark: Base vs QLoRA Fine-Tuned",
                 fontsize=14, fontweight="bold", color="#F8FAFC", pad=18)
    ax.set_ylabel("Score (%)", fontsize=11, color="#94A3B8")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=11, color="#F8FAFC")
    ax.set_ylim(0, 125)
    ax.yaxis.grid(True, linestyle="--", alpha=0.2, color="#CBD5E1", zorder=0)
    ax.xaxis.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors="#94A3B8", length=0)

    legend = ax.legend(frameon=True, facecolor="#1E293B", edgecolor="#334155",
                       fontsize=10, loc="upper left", bbox_to_anchor=(0.01, 0.99))
    for t in legend.get_texts():
        t.set_color("#E2E8F0")

    ft_types = ft["types"]
    breakdown = (f"Fine-Tuned predictions — "
                 f"INSERT: {ft_types['INSERT']}  "
                 f"UPDATE: {ft_types['UPDATE']}  "
                 f"DELETE: {ft_types['DELETE']}")
    plt.figtext(0.5, -0.03,
                f"Apple Silicon (M-series) | MLX Framework | Dataset: gretelai/synthetic_text_to_sql\n{breakdown}",
                ha="center", fontsize=9, color="#64748B")

    plt.tight_layout()
    plt.savefig(CHART_FILE, bbox_inches="tight")
    print(f"\nChart saved -> {CHART_FILE}")


if __name__ == "__main__":
    valid_path = Path(VALID_FILE)
    if not valid_path.exists():
        print(f"ERROR: {VALID_FILE} not found. Run data_dml_prep.py first.")
        sys.exit(1)

    with open(valid_path) as f:
        all_samples = [json.loads(line) for line in f]

    samples = all_samples[:SAMPLE_COUNT]
    print(f"Loaded {len(samples)} validation samples from {VALID_FILE}")

    with open(LOG_FILE, "w", encoding="utf-8") as log_f:
        log_f.write("DML BENCHMARK EXECUTION LOG\n" + "=" * 60 + "\n")

        # 1. Base model (no adapter)
        print("\n[1/2] Loading BASE model (no adapter)...")
        model_base, tokenizer = load(MODEL_ID)
        base_metrics = evaluate(model_base, tokenizer, samples, "Base Model", log_f)
        del model_base   # free memory before loading adapter

        # 2. Fine-tuned DML adapter
        print("\n[2/2] Loading DML FINE-TUNED adapter...")
        model_ft, _ = load(MODEL_ID, adapter_path=ADAPTER_PATH)
        ft_metrics = evaluate(model_ft, tokenizer, samples, "DML Fine-Tuned", log_f)

    # 3. Chart
    generate_chart(base_metrics, ft_metrics)

    print("\n Benchmark complete.")
    print(f"   Detailed log -> {LOG_FILE}")
    print(f"   Chart        -> {CHART_FILE}")
