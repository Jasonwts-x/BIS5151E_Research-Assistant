# Async/Sync Design Patterns

## Overview
Our system uses a hybrid async/sync approach for optimal performance.

---

## When to Use Sync vs Async

### ✅ Use SYNC (`def`) for:
1. **CPU-bound operations** (LLM inference, crew execution)
2. **Blocking operations** (file I/O if small/fast)
3. **Simple operations** (dict lookups, validation checks)

**Example:**
```python
def run_crew_sync(request: CrewRunRequest) -> CrewRunResponse:
    """Synchronous crew execution - blocks until complete."""
    result = runner.run(topic=request.topic, language=request.language)
    return CrewRunResponse(answer=result.final_output)
```

### ✅ Use ASYNC (`async def`) for:
1. **I/O-bound operations** (HTTP requests, database queries)
2. **Operations that can be parallelized**
3. **Long-running tasks with background execution**

**Example:**
```python
async def crewai_run(payload: CrewRunRequest) -> CrewRunResponse:
    """Async HTTP proxy - doesn't block while waiting for response."""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CREWAI_URL}/run", json=payload.dict())
        return CrewRunResponse(**response.json())
```

---

## Our Implementation

### API Gateway (`src/api/routers/crewai.py`)
- **All endpoints**: `async def`
- **Why**: Gateway just proxies HTTP requests (I/O-bound)
- **Benefit**: Can handle multiple concurrent requests without blocking
```python
async def crewai_run(payload: CrewRunRequest) -> CrewRunResponse:
    """Async proxy to crew service."""
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(f"{CREWAI_URL}/run", json=payload.model_dump())
        return CrewRunResponse(**response.json())
```

### CrewAI Service (`src/agents/api/routers/crewai.py`)

#### Sync Endpoint - Direct Execution
```python
def run_crew_sync(request: CrewRunRequest) -> CrewRunResponse:
    """
    Synchronous execution - blocks for 30-60 seconds.
    Use when: You can wait for the result.
    """
    result = runner.run(topic=request.topic, language=request.language)
    return CrewRunResponse(answer=result.final_output)
```

#### Async Endpoint - Background Execution
```python
async def run_crew_async(
    request: CrewRunRequest,
    background_tasks: BackgroundTasks,
) -> CrewAsyncRunResponse:
    """
    Async execution - returns immediately with job_id.
    Use when: You want to poll for results later.
    """
    job_id = manager.create_job(topic=request.topic, language=request.language)
    background_tasks.add_task(manager.execute_job, job_id)
    return CrewAsyncRunResponse(job_id=job_id, status="pending")
```

### Job Manager (`src/agents/api/jobs.py`)
- **Creates jobs**: `def create_job()` - Simple dict operation (sync)
- **Executes jobs**: `async def execute_job()` - Runs crew in thread pool
- **Gets status**: `def get_job()` - Simple dict lookup (sync)
```python
async def execute_job(self, job_id: str) -> None:
    """Run crew in thread pool to avoid blocking event loop."""
    loop = asyncio.get_event_loop()
    
    # Run CPU-bound crew execution in thread pool
    result = await loop.run_in_executor(
        None,  # Use default thread pool
        self.runner.run,
        job.topic,
        job.language,
    )
    
    job.result = result
    job.status = JobStatus.COMPLETED
```

---

## Performance Implications

### Sync Endpoint Performance
- **Throughput**: Limited by crew execution time (~30-60s)
- **Concurrency**: Limited by available workers (default: CPU count)
- **Best for**: n8n workflows that want immediate results

### Async Endpoint Performance
- **Throughput**: High - can queue hundreds of jobs
- **Concurrency**: Limited by thread pool (but much better than sync)
- **Best for**: Web UIs, batch processing, parallel workflows

---

## Testing Both Patterns

### Test Sync Endpoint
```bash
curl -X POST http://localhost:8000/crewai/run \
  -H "Content-Type: application/json" \
  -d '{"topic": "neural networks", "language": "en"}'
  
# Blocks for 30-60s, then returns result
```

### Test Async Endpoint
```bash
# 1. Submit job (returns immediately)
JOB_ID=$(curl -X POST http://localhost:8000/crewai/run/async \
  -H "Content-Type: application/json" \
  -d '{"topic": "neural networks", "language": "en"}' | jq -r '.job_id')

# 2. Poll for result
curl http://localhost:8000/crewai/status/$JOB_ID

# 3. When status=="completed", result field contains the output
```

---

## Common Pitfalls

### ❌ DON'T: Use async for CPU-bound work without executor
```python
async def bad_example():
    # This still blocks the event loop!
    result = slow_cpu_intensive_function()
    return result
```

### ✅ DO: Use thread/process pool for CPU-bound work
```python
async def good_example():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, slow_cpu_intensive_function
    )
    return result
```

### ❌ DON'T: Use async when sync is simpler
```python
# Unnecessary complexity
async def get_config():
    return await asyncio.to_thread(lambda: {"key": "value"})

# Just use sync
def get_config():
    return {"key": "value"}
```

---

## Summary

| Component | Pattern | Reason |
|-----------|---------|--------|
| API Gateway | Async | HTTP proxying (I/O-bound) |
| `/run` endpoint (crew service) | Sync | Crew execution (CPU-bound) |
| `/run/async` endpoint | Async | Background task queuing |
| Job executor | Async + thread pool | CPU-bound work in async context |
| Job status/lookup | Sync | Simple dict operations |
| RAG retrieval | Sync | Haystack/Weaviate client is sync |

This hybrid approach gives us:
- ✅ Good performance for I/O-bound operations
- ✅ Proper handling of CPU-bound operations
- ✅ Support for both blocking and non-blocking workflows
- ✅ Simple, maintainable code