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

def run_agent(question:str, schema:str,max_retries:int=2)->dict:
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
    final_state=app.invoke(initial_state)

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
            "retries": final_state['attempts'] - 1,
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
            "retries": final_state['attempts'] - 1,
            "data": None,
            "error": final_state['error_trace']
        }

    
    