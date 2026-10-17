import uuid
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from arq import create_pool
from arq.connections import RedisSettings

from api.cache import generate_cache_key, get_cached_query, redis_client
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Antigravity SQL Agent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    
    cached = await get_cached_query(cache_key)

    if cached and not request.force_refresh:
        task_id = f"cached_{uuid.uuid4().hex[:8]}"
        
        await redis_client.hset(f"task:{task_id}", mapping={
            "status": "completed",
            "sql": cached.get("sql", ""),
            "data": json.dumps(cached.get("data", [])),
            "retries": 0,
            "error": ""
        })

        # Save instant completed event for SSE stream
        cached_event = json.dumps({
            "event": "completed",
            "task_id": task_id,
            "data": {
                "status": "completed",
                "cached": True,
                "sql": cached.get("sql", ""),
                "data": cached.get("data", []),
                "retries": 0,
                "error": None,
                "message": "Instant deterministic cache hit (<5ms)"
            }
        })
        await redis_client.rpush(f"events:{task_id}", cached_event)
        await redis_client.expire(f"events:{task_id}", 3600)

        return TaskResponse(task_id=task_id, status="completed", cached=True)

    task_id = f"task_{uuid.uuid4().hex[:8]}"

    await redis_client.hset(f"task:{task_id}", mapping={"status": "queued"})

    # Initial queued event
    queued_event = json.dumps({
        "event": "queued",
        "task_id": task_id,
        "data": {
            "message": "Query enqueued. Waiting for GPU worker...",
            "step": "queued"
        }
    })
    await redis_client.rpush(f"events:{task_id}", queued_event)
    await redis_client.expire(f"events:{task_id}", 3600)

    await arq_pool.enqueue_job('process_sql_job', task_id, request.question, request.schema_ddl, cache_key)
    
    return TaskResponse(task_id=task_id, status="queued", cached=False)

@app.get("/api/tasks/{task_id}", response_model=TaskResultResponse)
async def get_task_status(task_id: str):
    """Poll the task status to see if the llm has finished writing the SQL"""
    task_data = await redis_client.hgetall(f"task:{task_id}")

    if not task_data:
        raise HTTPException(status_code=404, detail="task not found")
    
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

@app.get("/api/tasks/{task_id}/events")
async def get_task_events(task_id: str):
    """Server-Sent Events endpoint streaming live thought steps from Redis Pub/Sub"""
    async def event_generator():
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"channel:{task_id}")

        try:
            # 1. Replay historical events from Redis list so far
            existing_events = await redis_client.lrange(f"events:{task_id}", 0, -1)
            is_terminal = False
            for raw_evt in existing_events:
                yield f"data: {raw_evt}\n\n"
                try:
                    parsed = json.loads(raw_evt)
                    if parsed.get("event") in ("completed", "failed"):
                        is_terminal = True
                        break
                except Exception:
                    pass

            if is_terminal:
                return

            # 2. Stream live events from PubSub
            async for message in pubsub.listen():
                if message["type"] == "message":
                    raw_data = message["data"]
                    yield f"data: {raw_data}\n\n"
                    try:
                        parsed = json.loads(raw_data)
                        if parsed.get("event") in ("completed", "failed"):
                            break
                    except Exception:
                        pass
        finally:
            await pubsub.unsubscribe(f"channel:{task_id}")
            await pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

from agent.seeds import UNIFIED_DDL, SUGGESTED_QUERIES

@app.get("/api/schemas")
async def get_default_schemas():
    """Lists available default test schema and sample questions"""
    return {
        "ddl": UNIFIED_DDL,
        "sample_queries": SUGGESTED_QUERIES
    }