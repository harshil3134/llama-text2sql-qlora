from typing_extensions import TypedDict,Annotated
from mlx_lm import load,generate
from functools import lru_cache

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
    clean_sql = text.replace("```sql", "").replace("```", "").strip()
    return clean_sql

def generate_sql(state:AgentState)-> AgentState:
    """ Takes the current state, prompts the MLX model and updates the state with the generated SQL"""
    try:
        print(f"Generating SQL... {state['attempts']}/{state['max_attempts']}")
        state['attempts'] += 1
        
        system_prompt = "You are an expert SQL generator. Given a database scheme and a natural Language question, write the exact SQL query that answers the question."
        user_prompt = f"Schema:\n{state['schema']}\n\nQuestion:\n{state['question']}"
        
        chat_format = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        if state.get('error_trace'):
            chat_format.append({"role":"user","content":f"Previous result: {state.get('current_sql')} \n Previous error: {state['error_trace']}. Please fix the query."})

        model,tokenizer=load_model()

        prompt=tokenizer.apply_chat_template(chat_format,tokenize=False,add_generation_prompt=True)
        
        response=generate(model,tokenizer,prompt=prompt,max_tokens=256,verbose=False)

        state["current_sql"]=clean_sql(response)

        state['status']='validating'
        return state

    except Exception as e:
        state['error_trace']=str(e)
        state['status']='error'
    return state

        