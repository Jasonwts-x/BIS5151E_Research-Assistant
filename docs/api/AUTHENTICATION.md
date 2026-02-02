# Authentication

API authentication and authorization.

---

## ⚠️ Current Status

**Authentication**: Not implemented (local use only)

The current version is designed for local, single-user deployment and **does not include authentication**.

---

## 🔓 Current Access

All endpoints are publicly accessible:
- No API keys required
- No user accounts
- No rate limiting
- Trusted network only (localhost)

---

## 🔐 Future Implementation

**Planned**: v3.1.0 (Q4 2025)

### JWT Authentication

**Login**:
```bash
POST /auth/login
{
  "username": "user@example.com",
  "password": "password"
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Authenticated Request**:
```bash
curl -X POST http://localhost:8000/research/query \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"query":"What is AI?"}'
```

---

### API Keys

**Generate Key**:
```bash
POST /auth/api-keys
Authorization: Bearer <token>

Response:
{
  "key": "sk_live_abc123...",
  "name": "My Application",
  "created_at": "2025-02-02T10:00:00Z"
}
```

**Use Key**:
```bash
curl -X POST http://localhost:8000/research/query \
  -H "X-API-Key: sk_live_abc123..." \
  -d '{"query":"What is AI?"}'
```

---

### Planned Features

- ✅ JWT token-based authentication
- ✅ API key management
- ✅ User accounts
- ✅ Role-based access control (RBAC)
- ✅ Rate limiting per user/key
- ✅ Audit logging

See [ROADMAP.md](../../ROADMAP.md) for details.

---

## 🔒 Current Security

For local deployment:
- Network isolation (Docker internal network)
- Localhost-only binding
- Input validation (Guardrails)
- Content safety checks

---

## 📚 Related Documentation

- **[API Overview](README.md)** - Getting started
- **[Security Best Practices](../guides/BEST_PRACTICES.md#security)** - Security tips

---

**[⬅ Back to API Documentation](README.md)**
```