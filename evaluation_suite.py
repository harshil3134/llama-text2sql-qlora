import sqlite3
import json
import re
import mlx.core as mx
from mlx_lm import load, generate

def extract_json_sql(text):
    text = text.strip()
    # Strip markdown blocks if the model still adds them
    if text.startswith("```json"):
        text = text.split("```json")[1].split("```")[0].strip()
    elif text.startswith("```"):
        text = text.split("```")[1].split("```")[0].strip()
        
    try:
        data = json.loads(text)
        sql = data.get("sql", "")
        return sql.split(";")[0] + ";" if sql else text
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails completely
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

def run_model_eval(model, tokenizer, test_dbs, label, use_json=False):
    print(f"\n{'='*50}\n🚀 EVALUATING: {label} (JSON Mode: {use_json})\n{'='*50}")
    
    total_tests = 0
    passed_tests = 0

    for db in test_dbs:
        print(f"=======================================")
        print(f"🏥 Testing Database: {db['db_name']}")
        print(f"=======================================")
        schema = db['schema']
        
        for i, qa in enumerate(db['questions'], 1):
            # If QUICK_TEST is True, only run 1 question per database (5 total)
            if QUICK_TEST and i > 1:
                break
                
            total_tests += 1
            question = qa['question']
            
            # Override the prompt if using JSON structured output
            if use_json:
                system_prompt = "You are an expert SQL generator. Given a database schema and a natural Language question, write the exact SQL query that answers the question. You MUST output your response as a valid JSON object containing exactly one key called \"sql\" with the query as its value. Do not output any conversational text."
            else:
                system_prompt = "You are an expert SQL generator. Given a database scheme and a natural Language question, write the exact SQL query that answers the question."
                
            user_prompt = f"Schema:\n{schema}\n\nQuestion:\n{question}"
            
            chat_format = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            formatted_prompt = tokenizer.apply_chat_template(chat_format, tokenize=False, add_generation_prompt=True)
            output = generate(model, tokenizer, prompt=formatted_prompt, max_tokens=150, verbose=False)
            
            # In evaluation suite we always try to parse as JSON if use_json is True
            sql_query = extract_json_sql(output) if use_json else output.replace("```sql", "").replace("```", "").split(";")[0] + ";"
            
            expected_sql = qa['expected_sql']
            
            # Execute both queries
            ok_gen, res_gen = execute_query(schema, sql_query)
            ok_exp, res_exp = execute_query(schema, expected_sql)
            
            print(f"Q{i}: {question}")
            print(f"Generated SQL: {sql_query}")
            if ok_gen and ok_exp:
                # Compare results ignoring order
                if sorted(res_gen, key=str) == sorted(res_exp, key=str):
                    print(f"Status: ✅ Result MATCHES expected output! (Rows: {len(res_gen)})")
                    passed_tests += 1
                else:
                    print(f"Status: ❌ Result MISMATCH!\n  Expected: {res_exp}\n  Got:      {res_gen}")
            elif not ok_gen:
                print(f"Status: ❌ SQL Error in generated query: {res_gen}")
            else:
                print(f"Status: ❌ SQL Error in EXPECTED query: {res_exp}")
            print("-" * 50)

    print(f"\n🎯 {label} Final Score: {passed_tests}/{total_tests} queries matched the expected results!")
    return passed_tests, total_tests

def run_evaluation():
    # SET THIS TO FALSE TO RUN ALL 25 QUESTIONS!
    global QUICK_TEST
    QUICK_TEST = True
    
    print("Loading custom complex databases...")
    with open('test_dbs.json', 'r') as f:
        test_dbs = json.load(f)

    print("Loading Base Model...")
    model_base, tokenizer = load("mlx-community/Meta-Llama-3.1-8B-Instruct-4bit")
    run_model_eval(model_base, tokenizer, test_dbs, "Base Model", use_json=True)
    
    print("\nLoading Fine-Tuned Model...")
    model_ft, _ = load("mlx-community/Meta-Llama-3.1-8B-Instruct-4bit", adapter_path="./adapters")
    run_model_eval(model_ft, tokenizer, test_dbs, "Fine-Tuned Model", use_json=False)

if __name__ == "__main__":
    run_evaluation()
