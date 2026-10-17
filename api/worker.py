import asyncio
import json
from api.cache import redis_client, set_cached_query

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.graph import run_agent

async def process_sql_job(ctx, task_id: str, question: str, schema_ddl: str, cache_key: str):
    """ The background worker function that runs the MLX LangGraph LLM """
    
    # Update status to executing
    await redis_client.hset(f"task:{task_id}", mapping={"status": "executing"})

    loop = asyncio.get_running_loop()

    def on_step(event_type: str, data: dict):
        payload = json.dumps({
            "event": event_type,
            "task_id": task_id,
            "data": data
        })
        async def _publish():
            await redis_client.rpush(f"events:{task_id}", payload)
            await redis_client.expire(f"events:{task_id}", 3600)
            await redis_client.publish(f"channel:{task_id}", payload)

        asyncio.run_coroutine_threadsafe(_publish(), loop)

    # Initial worker dequeue event
    on_step("dequeued", {"message": "Task picked up by sequential GPU worker. Initializing MLX agent..."})
    
    try:
        # Run the agent in a separate thread so we don't block the asyncio event loop
        result = await asyncio.to_thread(run_agent, question=question, schema=schema_ddl, on_step=on_step)
        
        is_success = result.get("status") == "success"
        retries = result.get("retries", 0)

        result_payload = {
            "status": "completed" if is_success else "failed",
            "sql": result.get("sql", ""),
            "data": json.dumps(result.get("data", [])),
            "retries": retries,
            "error": result.get("error") or ""
        }
        
        # Save exact-query cache if successful
        if is_success:
            await set_cached_query(cache_key, result)

        # Update specific task status for polling fallback
        await redis_client.hset(f"task:{task_id}", mapping=result_payload)

        # Emit terminal event
        terminal_event = json.dumps({
            "event": "completed" if is_success else "failed",
            "task_id": task_id,
            "data": {
                "status": "completed" if is_success else "failed",
                "sql": result.get("sql", ""),
                "data": result.get("data", []),
                "retries": retries,
                "error": result.get("error"),
                "message": "Query generation & execution finished." if is_success else f"Query failed: {result.get('error')}"
            }
        })
        await redis_client.rpush(f"events:{task_id}", terminal_event)
        await redis_client.expire(f"events:{task_id}", 3600)
        await redis_client.publish(f"channel:{task_id}", terminal_event)

        return result
        
    except Exception as e:
        error_msg = str(e)
        await redis_client.hset(f"task:{task_id}", mapping={"status": "failed", "error": error_msg})
        failed_event = json.dumps({
            "event": "failed",
            "task_id": task_id,
            "data": {
                "status": "failed",
                "error": error_msg,
                "message": f"Worker encountered an unexpected error: {error_msg}"
            }
        })
        await redis_client.rpush(f"events:{task_id}", failed_event)
        await redis_client.expire(f"events:{task_id}", 3600)
        await redis_client.publish(f"channel:{task_id}", failed_event)
        raise e

from arq.connections import RedisSettings

class WorkerSettings:
    functions = [process_sql_job]
    redis_settings = RedisSettings()
    max_jobs = 1  # CRITICAL: Only 1 job at a time
