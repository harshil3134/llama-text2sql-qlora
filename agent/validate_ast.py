import sqlglot
from sqlglot import exp
from .agent import AgentState


def validate_ast(state:AgentState)-> AgentState:
    try:
        print(f"Validating AST... {state['current_sql']}")  
        sql=state["current_sql"]

        parsed=sqlglot.parse_one(sql,read="sqlite")

        if not isinstance(parsed,exp.Select):
            state["status"]="failed"
            state["error_trace"]=f"Security Violation:  ONly select statemets are allowed Found {type(parsed).__name__}"
            return state


        forbidden_types=[
            exp.Drop,
            exp.Delete,
            exp.Update,
            exp.Alter,
            exp.Insert,
            exp.Create,
            exp.Command,
        ]
            
        for forbidden in forbidden_types:
            # .find() searches the entire nested tree for that specific operation
            if parsed.find(forbidden):
                state["status"] = "failed"
                state["error_trace"] = f"Security Violation: Prohibited operation '{forbidden.__name__}' found in query."
                return state
       
        print("AST Validation Passed! ✅")
        state["status"] = "executing" # Move to the next step
        state["error_trace"] = None
        return state
    
    except sqlglot.errors.ParseError as e:
        # The LLM wrote invalid SQL that doesn't even compile
        print("AST Validation Failed! ❌")
        state["status"] = "failed"
        state["error_trace"] = f"SQL Syntax Error: {str(e)}"
        return state