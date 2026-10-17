from langgraph.graph import StateGraph,END
from .agent import AgentState,generate_sql
from .validate_ast import validate_ast
from .execute import execute_query


def should_continue(state: AgentState)-> str:

    """
    This is the traffic cop. It looks at the status written on the state clipboard and returns the name of the next to go to.
"""
    status=state.get("status")

    if status=="executing": 
        return "execute_node"

    elif status=="reflection_required":
        return "generate_node"
    elif status=="executed" or status=="failed":
        return END


workflow=StateGraph(AgentState)


workflow.add_node("generate_node",generate_sql)
workflow.add_node("validate_node",validate_ast)
workflow.add_node("execute_node",execute_query)

workflow.set_entry_point("generate_node")

workflow.add_edge("generate_node","validate_node")
workflow.add_conditional_edges("validate_node",should_continue)

workflow.add_conditional_edges("execute_node",should_continue)

app=workflow.compile()

def run_agent(question:str, schema:str, max_retries:int=2, on_step=None)->dict:
    """This is the clean function you can import into your streamlit ui or fastapi server"""

    initial_state={
        "question":question,
        "schema":schema,
        "current_sql":"",
        "attempts":0,
        "max_attempts":max_retries,
        "error_trace":None,
        "status":"generating",
        "result":None
    }

    print("starting agent...\n")
    if on_step:
        on_step("started", {"message": "Starting SQL agent workflow..."})

    final_state = initial_state
    for step in app.stream(initial_state):
        if "generate_node" in step:
            final_state = step["generate_node"]
            if on_step:
                on_step("generated_sql", {
                    "message": f"Drafted SQL query (Attempt {final_state['attempts']})",
                    "sql": final_state.get("current_sql", ""),
                    "attempt": final_state.get("attempts", 1)
                })
        elif "validate_node" in step:
            final_state = step["validate_node"]
            if on_step:
                if final_state.get("error_trace"):
                    on_step("validation_error", {
                        "message": f"AST Validation issue: {final_state['error_trace']}",
                        "error": final_state['error_trace']
                    })
                else:
                    on_step("validation_passed", {
                        "message": "AST Validation passed: Valid SELECT syntax verified."
                    })
        elif "execute_node" in step:
            final_state = step["execute_node"]
            if on_step:
                if final_state.get("status") == "executed":
                    count = len(final_state.get("result") or [])
                    on_step("execution_success", {
                        "message": f"Sandbox query executed successfully ({count} rows returned).",
                        "rows_count": count
                    })
                elif final_state.get("status") == "reflection_required":
                    on_step("reflection_triggered", {
                        "message": f"Execution error: {final_state.get('error_trace')}. Initiating self-correction...",
                        "error": final_state.get("error_trace")
                    })
                else:
                    on_step("execution_failed", {
                        "message": f"Execution failed: {final_state.get('error_trace')}",
                        "error": final_state.get("error_trace")
                    })

    print("\n==== SUMMARY ===")
    print(f"SQL Used: {final_state['current_sql']}")
    print(f"Status: {final_state['status']}")
    print(f"Retries: {final_state['attempts'] - 1}")
    print(f"Result Rows: {len(final_state['result']) if final_state['result'] else 0}")
    print("\n")

    if final_state['status'] == 'executed':
        return {
            "sql": final_state['current_sql'],
            "status": "success",
            "retries": max(0, final_state['attempts'] - 1),
            "data": final_state['result'],
            "error": None
        }
    else:
        final_status = "failed"
        if final_state.get('error_trace') and "Security Violation" in final_state['error_trace']:
            final_status = "blocked"
            
        return {
            "sql": final_state['current_sql'],
            "status": final_status,
            "retries": max(0, final_state['attempts'] - 1),
            "data": None,
            "error": final_state['error_trace']
        }

    
    