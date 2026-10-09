

def __main__():
    from agent.graph import run_agent

    result=run_agent(
        question="What is the average salary of employees in the sales department?",
        schema="CREATE TABLE employees (id INT, name VARCHAR(100), department VARCHAR(100), salary INT);",
        max_retries=2
    )
    print(result)


if __name__=="__main__":
    __main__() 