from typing_extensions import TypedDict,Annotated
from mlx_lm import load,generate
from functools import lru_cache
import re

class AgentState(TypedDict):
    question:str
    schema:str
    current_sql:str
    attempts:int
    max_attempts:int
    error_trace:str|None
    status:str
    result:list[dict]|None




MODEL_ID = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
ADAPTER_PATH = "./adapters"

@lru_cache(maxsize=1)
def load_model():
    return load(MODEL_ID, adapter_path=ADAPTER_PATH)

def clean_sql(text:str)->str:
    text=text.strip()

    sql_match=re.search(r'<sql>(.*?)(?:</sql>|$)',text, re.IGNORECASE | re.DOTALL)

    if sql_match:
        return sql_match.group(1).strip()
    else:
        return text.replace("```sql", "").replace("```", "").strip()

def generate_sql(state:AgentState)-> AgentState:
    """ Takes the current state, prompts the MLX model and updates the state with the generated SQL"""
    try:
        print(f"Generating SQL... {state['attempts']}/{state['max_attempts']}")
        state['attempts'] += 1
        
        if state['attempts']==1:
            system_prompt=("You are an expert SQL generator. Given a database schema and a natural language question, write the exact SQL query that answers the question. "
             "Then, output the final SQL query inside <sql></sql> tags."
        ) 
        else:
            system_prompt = (
            "You are an expert SQL generator. Given a database schema and a natural language question, write the exact SQL query that answers the question. "
            "First, think step-by-step inside <thought></thought> tags to analyze the tables and identify which columns belong to which tables. Keep your thought process extremely short and concise (under 3 sentences). "
            "Then, output the final SQL query inside <sql></sql> tags."
        ) 
        user_prompt = f"Schema:\n{state['schema']}\n\nQuestion:\n{state['question']}"
        
        chat_format = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        if state.get('error_trace'):
            print("error trace exists   ",state.get("error_trace"))
            chat_format.extend([
                {"role":"assistant","content":state.get("current_sql")},
                {"role":"user","content":f" Previous error: {state['error_trace']}. Please fix the query. First explain what went wrong inside <thought> tags, then return the fixed query inside <sql> tags."}
            ])

        model,tokenizer=load_model()

        prompt=tokenizer.apply_chat_template(chat_format,tokenize=False,add_generation_prompt=True)
        
        response=generate(model,tokenizer,prompt=prompt,max_tokens=1024,verbose=False)

        print("raw response: ", response)
        state["current_sql"]=clean_sql(response)

        state['status']='validating'
        return state

    except Exception as e:
        state['error_trace']=str(e)
        state['status']='error'
    return state

        