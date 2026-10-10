import uuid
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from arq import create_pool
from arq.connections import RedisSettings

from api.cache import generate_cache_key, get_cached_query, redis_client

app = FastAPI(title="Antigravity SQL Agent Backend")

class QueryRequest(BaseModel):
    question: str
    schema_ddl: str
    force_refresh: bool = False
    
class TaskResponse(BaseModel):
    task_id: str
    status: str
    cached: bool

class TaskResultResponse(BaseModel):
    task_id: str
    status: str
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    retries: int = 0
    error: Optional[str] = None

arq_pool = None

@app.on_event("startup")
async def startup():
    global arq_pool
    arq_pool = await create_pool(RedisSettings())

@app.post("/api/query", response_model=TaskResponse, status_code=202)
async def submit_query(request: QueryRequest):
    cache_key = generate_cache_key(request.question, request.schema_ddl)
    
    # FIX 1: Add await here!
    cached = await get_cached_query(cache_key)

    if cached and not request.force_refresh:
        task_id = f"cached_{uuid.uuid4().hex[:8]}"
        
        # FIX 2: redis_client was not imported!
        await redis_client.hset(f"task:{task_id}", mapping={
            "status": "completed",
            "sql": cached.get("sql", ""),
            "data": json.dumps(cached.get("data", [])),
            "retries": 0,
            "error": ""
        })
        return TaskResponse(task_id=task_id, status="completed", cached=True)

    task_id = f"task_{uuid.uuid4().hex[:8]}"

    await redis_client.hset(f"task:{task_id}", mapping={"status": "queued"})
    await arq_pool.enqueue_job('process_sql_job', task_id, request.question, request.schema_ddl, cache_key)
    
    return TaskResponse(task_id=task_id, status="queued", cached=False)

@app.get("/api/tasks/{task_id}", response_model=TaskResultResponse)
async def get_task_status(task_id: str):
    """Poll the task status to see if the llm has finished writing the SQL"""
    task_data = await redis_client.hgetall(f"task:{task_id}")

    if not task_data:
        raise HTTPException(status_code=404, detail="task not found")
    
    # FIX 3: Parse the string data back into Python objects
    parsed_data = None
    if "data" in task_data and task_data["data"]:
        parsed_data = json.loads(task_data["data"])
        
    return TaskResultResponse(
        task_id=task_id,
        status=task_data.get("status", "unknown"),
        sql=task_data.get("sql"),
        data=parsed_data,
        retries=int(task_data.get("retries", 0)),
        error=task_data.get("error")
    )