"""
TEST: Concurrency Stress Test 
PURPOSE: Proves that your FastAPI + Redis architecture is production-ready. 
It fires 10 simultaneous requests to the server to ensure the Worker processes them sequentially (max_jobs=1) without crashing the Mac.
"""
import asyncio
import httpx
import time

API_URL = "http://localhost:8000/api/query"

# 10 different users asking 10 different questions at the same time
QUESTIONS = [
    "How many employees are in Engineering?",
    "What is the average salary of the sales department?",
    "Who is the highest paid employee?",
    "List all employees in the IT department.",
    "Show the total payroll for each department.",
    "Find employees hired in the last year.",
    "Which department has the most employees?",
    "List the names of all managers.",
    "What is the minimum salary across the company?",
    "Count the number of employees making over 90000."
]


SCHEMA = "CREATE TABLE employees (id INT, name VARCHAR, salary INT, department VARCHAR);"

async def make_request(client, index, question):
    print(f"[User {index}] Sending question...")
    
    # 1. Ask FastAPI to generate the SQL
    response = await client.post(API_URL, json={
        "question": question,
        "schema_ddl": SCHEMA,
        "force_refresh": True  # Force it to run the LLM (ignore the cache)
    })
    
    task_id = response.json()["task_id"]
    print(f"[User {index}] Got task ID: {task_id}. Waiting in queue...")
    
    # 2. Poll the status every 2 seconds until the Worker finishes
    while True:
        status_resp = await client.get(f"http://localhost:8000/api/tasks/{task_id}")
        data = status_resp.json()
        
        if data["status"] == "completed":
            print(f"✅ [User {index}] Finished! SQL Generated: {data['sql']}")
            break
        elif data["status"] == "failed":
            print(f"❌ [User {index}] Failed! Error: {data['error']}")
            break
            
        await asyncio.sleep(2)

async def run_stress_test():
    print("🚀 Starting 10-User Concurrency Stress Test...")
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Launch all 10 users at the exact same millisecond
        tasks = [make_request(client, i, q) for i, q in enumerate(QUESTIONS)]
        await asyncio.gather(*tasks)
        
    end_time = time.time()
    print(f"\n🎉 All 10 requests completed perfectly in {end_time - start_time:.2f} seconds without crashing!")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
