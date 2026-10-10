import asyncio
import json
from api.cache import redis_client, set_cached_query

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from test_phase_1 import run_agent

async def process_sql_job(ctx, task_id: str, question: str, schema_ddl: str, cache_key: str):
    """ The background worker function that runs the MLX LangGraph LLM """
    
    # Update status to executing
    await redis_client.hset(f"task:{task_id}", mapping={"status": "executing"})
    
    try:
        # Run the agent in a separate thread so we don't block the asyncio event loop!
        result = await asyncio.to_thread(run_agent, question=question, schema=schema_ddl)
        
        attempts = result.get("attempts", 1)
        retries = max(0, attempts - 1)

        result_payload = {
            "status": "completed",
            "sql": result.get("current_sql", ""),
            "data": json.dumps(result.get("data", [])),
            "retries": retries,
            "error": ""
        }
        
        # Save exact-query cache (so future identical queries skip the LLM)
        await set_cached_query(cache_key, result)

        # Update specific task status for the frontend
        await redis_client.hset(f"task:{task_id}", mapping=result_payload)
        return result
        
    except Exception as e:
        await redis_client.hset(f"task:{task_id}", mapping={"status": "failed", "error": str(e)})
        raise e

class WorkerSettings:
    functions = [process_sql_job]
    redis_settings = "redis://localhost:6379"
    max_jobs = 1  # CRITICAL: Only 1 job at a time
