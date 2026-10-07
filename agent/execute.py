import sqlite3
from .agent import AgentState

def execute_query(state:AgentState)-> AgentState:
    """
    Spins up a temporary SQLite sandbox builds the tables using the schema, and tries to run the generated SQL."""

    print("Executing Query... \n")

    conn=sqlite3.connect(":memory:")

    conn.row_factory=sqlite3.Row
    cursor=conn.cursor()

    try:
        cursor.executescript(state['schema'])

        cursor.execute(state['current_sql'])

        rows=cursor.fetchall()
        
        result_data=[dict(row) for row in rows]

        print(f"Query Execution   passed {len(result_data)} rows")

        state['result']=result_data
        state["status"]="executed"
        state["error_trace"]=None
        return state
    except Exception as e:
        print(f"Execution Failed: {e}")
        state["status"]="failed"
        state["error_trace"]=str(e)

        if state['attempts']<state['max_attempts']:
            state['status']='reflection_required'
        return state
    finally:
        conn.close()