# Deployment Guide

Production deployment instructions.

---

## Prerequisites

- Docker & Docker Compose
- 4GB RAM minimum
- 10GB disk space

---

## Production Configuration

### 1. Environment Variables

Create `.env` file:
```bash
# Required
POSTGRES_PASSWORD=<strong-password>
N8N_ENCRYPTION_KEY=<random-key>

# Optional
TRULENS_ENABLED=true
GUARDRAILS_STRICT_MODE=true
```

### 2. Security

**Disable anonymous Weaviate access:**
```yaml
# docker-compose.yml
environment:
  AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "false"
  AUTHENTICATION_APIKEY_ENABLED: "true"
  AUTHENTICATION_APIKEY_ALLOWED_KEYS: "${WEAVIATE_API_KEY}"
```

### 3. Resource Limits
```yaml
services:
  eval:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

---

## Monitoring

### Health Checks
```bash
curl http://localhost:8000/health
curl http://localhost:8100/health
curl http://localhost:8502/health
```

### Logs
```bash
docker compose logs -f eval
docker compose logs -f crewai
```

---

## Backup

### Database Backup
```bash
docker compose exec postgres pg_dump -U postgres trulens > backup.sql
```

### Restore
```bash
cat backup.sql | docker compose exec -T postgres psql -U postgres trulens
```

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)