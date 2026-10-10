from agent import validate_ast
from agent import validate_ast
import hashlib
import json
import redis.asyncio as redis

redis_client=redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

def generate_cache_key(question:str,schema_ddl:str)->str:
    """Computes a determinsitic hash based on the exact questin and schema."""

    combined=f"{question.strip()}_{schema_ddl.strip()}"

    hash_obj=hashlib.sha256(combined.encode('utf-8')).hexdigest()
    print("key",hash_obj)
    return f"sql_cache:{hash_obj}"


async def get_cached_query(key:str)->dict:
    data=await redis_client.get(key)

    if data:
        return json.loads(data)
    return None

async def set_cached_query(key:str, result_payload:dict, ttl:int=3600):
    await redis_client.setex(key, ttl, json.dumps(result_payload))