import sqlite3
from .agent import AgentState
from .seeds import UNIFIED_DDL, UNIFIED_SEED_SQL

def execute_query(state:AgentState)-> AgentState:
    """
    Spins up a temporary SQLite sandbox, builds the multi-table schema,
    populates realistic seed rows, and runs the generated SQL.
    """

    print("Executing Query... \n")

    conn=sqlite3.connect(":memory:")

    conn.row_factory=sqlite3.Row
    cursor=conn.cursor()

    try:
        # 1. Build unified multi-table database schema
        cursor.executescript(UNIFIED_DDL)

        # If user passed custom DDL that differs, execute it as well
        if state.get('schema') and state['schema'].strip() != UNIFIED_DDL.strip():
            try:
                cursor.executescript(state['schema'])
            except Exception:
                pass

        # 2. Populate all relational seed data (departments, employees, customers, orders)
        cursor.executescript(UNIFIED_SEED_SQL)

        # 3. Run generated SQL
        cursor.execute(state['current_sql'])

        rows=cursor.fetchall()
        
        result_data=[dict(row) for row in rows]

        print(f"Query Execution passed {len(result_data)} rows")

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