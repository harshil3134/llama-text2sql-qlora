import json
import random
import re
import sqlite3
from pathlib import Path
from datasets import load_dataset
import sqlglot
from sqlglot import exp

OUTPUT_DIR = Path("./data_dml")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = (
    "You are a database engineer. Return ONLY raw, executable DML SQL statements "
    "(INSERT, UPDATE, DELETE). Never include explanations, greetings, or markdown code fences. "
    "All UPDATE and DELETE queries MUST contain an explicit WHERE clause."
)

# MySQL / PostgreSQL functions that don't exist in SQLite
BANNED_PATTERNS = re.compile(
    r"\b(DATE_SUB|DATE_ADD|DATE_FORMAT|DATEDIFF|DATEADD|GETDATE|CURDATE|NOW\(\)|"
    r"YEAR\s*\(|MONTH\s*\(|DAY\s*\(|TIMESTAMPDIFF|FROM_UNIXTIME|UNIX_TIMESTAMP|"
    r"STR_TO_DATE|IFNULL\s*\(|ISNULL\s*\(|NVL\s*\(|IIF\s*\(|"
    r"EXTRACT\s*\(|TO_DATE|TO_CHAR|CONVERT\s*\(|TRY_CAST|"
    r"OVER\s*\(|PARTITION\s+BY|SCHEMA\.)\b",
    re.IGNORECASE
)


def is_safe_dml(sql: str) -> bool:
    """Ensure query is valid DML and contains WHERE for updates/deletes."""
    try:
        parsed = sqlglot.parse_one(sql, read="sqlite")
        if not isinstance(parsed, (exp.Insert, exp.Update, exp.Delete)):
            return False
        if isinstance(parsed, (exp.Update, exp.Delete)) and not parsed.find(exp.Where):
            return False
        return True
    except Exception:
        return False


def uses_banned_syntax(sql: str) -> bool:
    """Return True if SQL contains MySQL/PostgreSQL-specific syntax."""
    return bool(BANNED_PATTERNS.search(sql))


def sqlite_dry_run(schema_ddl: str, dml_sql: str) -> bool:
    """
    Try to execute the DML on a real in-memory SQLite instance.
    Returns True only if the statement executes without any error.
    The DML is rolled back — no data is permanently written.
    """
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    try:
        cur.executescript(schema_ddl)
        conn.execute("BEGIN")
        cur.execute(dml_sql)
        conn.rollback()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def clean_sql(sql: str) -> str:
    return sql.strip().rstrip(";") + ";"


def extract_ddl(context: str) -> str:
    """Extract only CREATE TABLE and INSERT statements from context."""
    lines = []
    for stmt in context.split(";"):
        s = stmt.strip().upper()
        if s.startswith("CREATE") or s.startswith("INSERT"):
            lines.append(stmt.strip() + ";")
    return "\n".join(lines)


def main():
    print("Loading gretelai/synthetic_text_to_sql (streaming)...")
    ds = load_dataset("gretelai/synthetic_text_to_sql", split="train", streaming=True)

    formatted_samples = []
    scanned = 0
    rejected_ast = 0
    rejected_syntax = 0
    rejected_sqlite = 0
    target_count = 1400

    for row in ds:
        if row.get("sql_task_type") != "data manipulation":
            continue

        scanned += 1
        sql      = row.get("sql", "")
        context  = row.get("sql_context", "")
        question = row.get("sql_prompt", "")

        if not (sql and context and question):
            continue

        # Gate 1: AST must be safe DML with WHERE on UPDATE/DELETE
        if not is_safe_dml(sql):
            rejected_ast += 1
            continue

        # Gate 2: No MySQL/PostgreSQL-only functions
        if uses_banned_syntax(sql) or uses_banned_syntax(context):
            rejected_syntax += 1
            continue

        # Gate 3: Must actually execute on SQLite without error
        ddl = extract_ddl(context)
        formatted_sql = clean_sql(sql)
        if not sqlite_dry_run(ddl, formatted_sql):
            rejected_sqlite += 1
            continue

        # All gates passed — keep this sample
        user_msg = f"Schema:\n{context}\n\nQuestion: {question}"
        formatted_samples.append({
            "messages": [
                {"role": "system",    "content": SYSTEM_PROMPT},
                {"role": "user",      "content": user_msg},
                {"role": "assistant", "content": formatted_sql}
            ]
        })

        if len(formatted_samples) % 100 == 0:
            print(f"  Collected {len(formatted_samples)} / {target_count}  "
                  f"(scanned {scanned}, rejected: ast={rejected_ast} "
                  f"syntax={rejected_syntax} sqlite={rejected_sqlite})")

        if len(formatted_samples) >= target_count:
            break

    print(f"\nFinal: {len(formatted_samples)} validated SQLite-safe DML samples")
    print(f"  Rejected — AST/WHERE: {rejected_ast}  |  "
          f"MySQL syntax: {rejected_syntax}  |  SQLite execution: {rejected_sqlite}")

    # Shuffle and split 90/10
    random.seed(42)
    random.shuffle(formatted_samples)
    split = int(len(formatted_samples) * 0.9)

    train_data = formatted_samples[:split]
    valid_data = formatted_samples[split:]

    with open(OUTPUT_DIR / "train.jsonl", "w") as f:
        for item in train_data:
            f.write(json.dumps(item) + "\n")

    with open(OUTPUT_DIR / "valid.jsonl", "w") as f:
        for item in valid_data:
            f.write(json.dumps(item) + "\n")

    print(f"\nSaved {len(train_data)} → {OUTPUT_DIR}/train.jsonl")
    print(f"Saved {len(valid_data)} → {OUTPUT_DIR}/valid.jsonl")


if __name__ == "__main__":
    main()