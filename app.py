import streamlit as st
import sqlite3
import re
import pandas as pd
from mlx_lm import load, generate

st.set_page_config(page_title="Text-to-SQL AI", layout="wide")

MODEL_ID = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
ADAPTER_PATH = "./adapters"

# @st.cache_resource  # Removed to fix MLX thread-local Stream(gpu, 1) errors
def load_model():
    return load(MODEL_ID, adapter_path=ADAPTER_PATH)

def clean_sql(text):
    text = re.sub(r"```sql|```", "", text).strip()
    return text.split(";")[0] + ";"

def execute_query(schema_ddl, query):
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    try:
        cur.executescript(schema_ddl)
        cur.execute(query)
        res = cur.fetchall()
        cols = []
        if cur.description:
            seen = {}
            for description in cur.description:
                base_name = description[0]
                if base_name in seen:
                    seen[base_name] += 1
                    cols.append(f"{base_name}_{seen[base_name]}")
                else:
                    seen[base_name] = 0
                    cols.append(base_name)
        return True, cols, res
    except Exception as e:
        return False, [], str(e)
    finally:
        conn.close()

st.title("🗄️ Chat with your Database (Text-to-SQL)")

with st.spinner("Loading AI Model (this takes a few seconds)..."):
    model, tokenizer = load_model()

# Sidebar for schema
with st.sidebar:
    st.header("Database Schema")
    st.markdown("Define your tables and insert sample data here.")
    default_schema = """CREATE TABLE employees (
    id INTEGER, 
    name VARCHAR, 
    department VARCHAR, 
    salary INTEGER
);

INSERT INTO employees VALUES (1, 'Alice', 'Engineering', 120000);
INSERT INTO employees VALUES (2, 'Bob', 'Sales', 80000);
INSERT INTO employees VALUES (3, 'Charlie', 'Engineering', 110000);
INSERT INTO employees VALUES (4, 'Diana', 'HR', 95000);"""
    
    schema_input = st.text_area("DDL & Inserts:", height=400, value=default_schema)

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sql" in msg:
            st.code(msg["sql"], language="sql")
        if "data" in msg:
            st.dataframe(msg["data"])

# Chat input
if prompt := st.chat_input("Ask a question about your data (e.g., 'Who is the highest paid engineer?'):"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Writing SQL..."):
            system_prompt = "You are an expert SQL generator. Given a database scheme and a natural Language question, write the exact SQL query that answers the question."
            user_prompt = f"Schema:\n{schema_input}\n\nQuestion:\n{prompt}"
            
            chat_format = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            formatted_prompt = tokenizer.apply_chat_template(chat_format, tokenize=False, add_generation_prompt=True)
            output = generate(model, tokenizer, prompt=formatted_prompt, max_tokens=150, verbose=False)
            
            sql_query = clean_sql(output)
            
            st.markdown("Here is the generated query:")
            st.code(sql_query, language="sql")
            
            ok, cols, res = execute_query(schema_input, sql_query)
            
            if ok:
                if res:
                    df = pd.DataFrame(res, columns=cols)
                    st.dataframe(df)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "Here is the result:", 
                        "sql": sql_query, 
                        "data": df
                    })
                else:
                    st.info("Query executed successfully but returned no results.")
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "Query returned no results.", 
                        "sql": sql_query
                    })
            else:
                st.error(f"SQL Error: {res}")
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"SQL Error: {res}", 
                    "sql": sql_query
                })

# Free memory at the end of each run to avoid OOM
import gc
import mlx.core as mx
del model, tokenizer
gc.collect()
mx.clear_cache()

