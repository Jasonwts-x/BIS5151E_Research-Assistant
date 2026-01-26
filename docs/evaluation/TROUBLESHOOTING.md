# Evaluation Troubleshooting Guide

Common issues and solutions for the evaluation service.

---

## Dashboard Not Loading

### Symptom
Browser shows "This site can't be reached" at http://localhost:8501

### Solutions

**1. Check if eval service is running:**
```powershell
docker ps | Select-String eval
```

**2. Check logs:**
```powershell
docker logs eval
```

**3. Verify port not in use:**
```powershell
netstat -ano | Select-String ":8501"
```

**4. Restart service:**
```powershell
docker compose -f docker/docker-compose.yml restart eval
```

**5. Rebuild if necessary:**
```powershell
cd docker
docker compose build eval
docker compose up -d eval
cd ..
```

---

## No Evaluation Data in Dashboard

### Symptom
Dashboard loads but shows "No data available"

### Solutions

**1. Run at least one query first:**
```powershell
$body = @{ topic = "What is AI?"; language = "en" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/rag/query" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 300
```

**2. Check database connection:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8502/health/ready"
```

**3. Check if records exist:**
```powershell
docker exec -it postgres psql -U postgres -d trulens -c "SELECT COUNT(*) FROM records;"
```

**4. Check leaderboard API:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8502/metrics/leaderboard"
```

---

## Evaluation API Returns 500 Error

### Symptom
`POST /metrics/evaluate` returns 500 Internal Server Error

### Solutions

**1. Check eval service logs:**
```powershell
docker logs eval --tail 50
```

**2. Check database connectivity:**
```powershell
docker exec -it eval python -c "from src.eval.database import get_database; db = get_database(); print(db.health_check())"
```

**3. Verify PostgreSQL is running:**
```powershell
docker ps | Select-String postgres
```

**4. Check database tables exist:**
```powershell
docker exec -it postgres psql -U postgres -d trulens -c "\dt"
```

Should show: records, performance_metrics, quality_metrics, guardrails_results

**5. Recreate tables if missing:**
```powershell
docker exec -it eval python -c "from src.eval.models import Base; from src.eval.database import get_database; Base.metadata.create_all(bind=get_database().engine)"
```

---

## Database Connection Failed

### Symptom
"Database not available" or connection timeout errors

### Solutions

**1. Check PostgreSQL container:**
```powershell
docker ps | Select-String postgres
docker logs postgres
```

**2. Verify DATABASE_URL environment variable:**
```powershell
docker exec -it eval env | Select-String DATABASE_URL
```

Should be: `postgresql://postgres:postgres@postgres:5432/trulens`

**3. Test database connection:**
```powershell
docker exec -it postgres psql -U postgres -d trulens -c "SELECT 1;"
```

**4. Check network connectivity:**
```powershell
docker exec -it eval ping postgres
```

**5. Restart PostgreSQL:**
```powershell
docker compose -f docker/docker-compose.yml restart postgres
```

---

## TruLens Metrics Show 0.0

### Symptom
All TruLens scores (groundedness, relevance) are 0.0

### Explanation
This is expected with the current heuristic implementation. Scores are based on:
- **Groundedness**: Citation check + keyword overlap
- **Relevance**: Query/answer keyword overlap
- **Context Relevance**: Query/context keyword overlap

Low scores usually mean:
- Answer lacks citations
- Low keyword overlap between query and answer
- Short or generic answers

### Solutions

**1. Check answer has citations:**
Answer should include `[1]`, `[2]` references.

**2. Ensure query terms appear in answer:**
If query is "machine learning", answer should mention those terms.

**3. For production, consider:**
- Implementing full TruLens with LLM-based evaluation
- Using OpenAI API for feedback functions
- Custom evaluation logic for your domain

---

## Guardrails Always Failing

### Symptom
`output_passed: false` for all queries

### Solutions

**1. Check guardrails configuration:**
```powershell
docker exec -it eval cat configs/guardrails.yaml
```

**2. Review violations:**
```powershell
# From query response
$response.evaluation.guardrails.violations
```

**3. Common issues:**
- **Missing citations**: Add `[1]` `[2]` references
- **Hallucination markers**: Avoid "I think", "I believe", "probably"
- **Length violations**: Keep answers within limits
- **Harmful content**: Check for inappropriate language

**4. Adjust guardrails for development:**
```yaml
# configs/guardrails.yaml
strict_mode: false  # More lenient
```

**5. Disable specific validators:**
Edit `src/eval/guardrails/validators/output.py` to skip checks.

---

## Performance Metrics Missing

### Symptom
`evaluation.performance` is null or incomplete

### Solutions

**1. Check PerformanceTracker is enabled:**
```powershell
docker exec -it crewai python -c "from src.agents.runner import CrewRunner; runner = CrewRunner(); print(runner.performance_tracker)"
```

**2. Verify timing data stored:**
```powershell
docker exec -it postgres psql -U postgres -d trulens -c "SELECT * FROM performance_metrics LIMIT 1;"
```

**3. Check for errors in logs:**
```powershell
docker logs crewai | Select-String "performance"
```

---

## Redis Cache Not Working

### Symptom
Redis cache shows as disabled or errors in logs

### Solutions

**1. Check Redis container:**
```powershell
docker ps | Select-String redis
```

**2. Verify REDIS_URL is set:**
```powershell
docker exec -it eval env | Select-String REDIS_URL
```

**3. Test Redis connection:**
```powershell
docker exec -it eval python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

**4. Check redis package installed:**
```powershell
docker exec -it eval pip list | Select-String redis
```

**5. Install if missing:**
```powershell
docker exec -it eval pip install redis hiredis
```

---

## Slow Evaluation (>10s)

### Symptom
Evaluation takes longer than 10 seconds

### Causes
- Database queries slow
- No caching enabled
- TruLens evaluation overhead
- Network latency

### Solutions

**1. Enable caching:**
```yaml
# docker-compose.yml
environment:
  REDIS_URL: redis://redis:6379/0
```

**2. Check database indexes:**
```powershell
docker exec -it postgres psql -U postgres -d trulens -c "\d records"
```

Ensure indexes exist on: record_id, ts

**3. Profile slow queries:**
```powershell
docker exec -it postgres psql -U postgres -d trulens -c "EXPLAIN ANALYZE SELECT * FROM records ORDER BY ts DESC LIMIT 100;"
```

**4. Increase database resources:**
```yaml
# docker-compose.yml
postgres:
  deploy:
    resources:
      limits:
        memory: 2G
```

---

## Port Already in Use

### Symptom
"Bind for 0.0.0.0:8501 failed: port is already allocated"

### Solutions

**1. Find process using port:**
```powershell
# For port 8501
netstat -ano | Select-String ":8501"

# For port 8502
netstat -ano | Select-String ":8502"
```

**2. Kill process:**
```powershell
# Get PID from netstat output
Stop-Process -Id <PID> -Force
```

**3. Or change port in docker-compose.yml:**
```yaml
eval:
  ports:
    - "8501:8501"  # Change to "8601:8501"
    - "8502:8502"  # Change to "8602:8502"
```

---

## Async Evaluation Not Working

### Symptom
Async endpoints return errors or don't complete

### Solutions

**1. Check if async methods implemented:**
```powershell
docker exec -it eval grep -r "async def evaluate" src/eval/
```

**2. Verify asyncio support:**
```powershell
docker exec -it eval python -c "import asyncio; print(asyncio.get_event_loop())"
```

**3. Check logs for async errors:**
```powershell
docker logs eval | Select-String "async"
```

---

## Need Help?

**Check logs first:**
```powershell
# All services
docker compose -f docker/docker-compose.yml logs

# Specific service
docker logs eval -f
docker logs crewai -f
docker logs postgres -f
```

**Verify environment:**
```powershell
docker exec -it eval env
```

**Test components individually:**
```powershell
# Database
docker exec -it postgres psql -U postgres -d trulens

# Python imports
docker exec -it eval python -c "from src.eval.database import get_database; print('OK')"

# API connectivity
Invoke-RestMethod -Uri "http://localhost:8502/health"
```

**Full restart:**
```powershell
cd docker
docker compose down -v
docker compose up -d
cd ..
```