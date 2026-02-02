# Setup & Installation Documentation

Complete guides for installing and configuring ResearchAssistantGPT.

---

## 📋 Quick Navigation

| Guide | Description | When to Use |
|-------|-------------|-------------|
| **[⚡ QUICKSTART](../../QUICKSTART.md)** | Get running in 5 minutes | First-time setup, want to try it quickly |
| **[📖 INSTALLATION](INSTALLATION.md)** | Complete step-by-step setup | Detailed installation, troubleshooting |
| **[🔌 N8N Setup](N8N.md)** | Workflow automation configuration | After basic installation, want automation |
| **[🚀 GPU Setup](GPU.md)** | NVIDIA GPU acceleration | Want faster inference (3-5x speedup) |
| **[🔧 TROUBLESHOOTING](TROUBLESHOOTING.md)** | Common issues and solutions | Something's not working |

---

## 🎯 Installation Path

Follow this recommended path for setup:
```
1. Prerequisites Check
   ↓
2. Basic Installation (QUICKSTART or INSTALLATION)
   ↓
3. Verify Services (health checks)
   ↓
4. First Query (test the system)
   ↓
5. [Optional] GPU Setup (if you have NVIDIA GPU)
   ↓
6. [Optional] n8n Setup (for automation)
   ↓
7. Start Using!
```

---

## 📚 Guide Overview

### Quick Start
**File**: [QUICKSTART.md](../../QUICKSTART.md) (in root directory)

**Covers**:
- ✅ Minimal prerequisites
- ✅ Clone and configure
- ✅ Start services
- ✅ First query in 5 minutes

**Best for**:
- First-time users
- Quick evaluation
- Demo purposes

---

### Complete Installation
**File**: [INSTALLATION.md](INSTALLATION.md)

**Covers**:
- ✅ System requirements (detailed table)
- ✅ Prerequisites installation (Docker, Git)
- ✅ Repository setup
- ✅ Environment configuration (both .env files)
- ✅ Service startup and verification
- ✅ Common startup issues
- ✅ First query examples

**Best for**:
- Detailed step-by-step guidance
- Understanding each component
- Troubleshooting setup issues

---

### n8n Workflow Setup
**File**: [N8N.md](N8N.md)

**Covers**:
- ✅ Creating n8n admin account
- ✅ Understanding n8n interface
- ✅ Importing example workflows
- ✅ Configuring API credentials
- ✅ Testing workflows
- ✅ Creating custom workflows
- ✅ Scheduling automated research

**Best for**:
- After basic installation
- Want workflow automation
- Scheduled research tasks
- Email notifications

---

### GPU Acceleration
**File**: [GPU.md](GPU.md)

**Covers**:
- ✅ NVIDIA GPU requirements
- ✅ NVIDIA Container Toolkit installation
- ✅ Docker GPU configuration
- ✅ Starting with GPU support
- ✅ Verifying GPU usage
- ✅ Performance comparisons

**Best for**:
- Users with NVIDIA GPUs
- Want 3-5x faster inference
- Working with large models

**Note**: Only NVIDIA GPUs supported currently (AMD experimental)

---

### Troubleshooting
**File**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**Covers**:
- ✅ Common startup errors
- ✅ Port conflicts
- ✅ Service connection issues
- ✅ Ollama problems
- ✅ Weaviate issues
- ✅ n8n database errors
- ✅ Docker resource problems
- ✅ Network connectivity
- ✅ Diagnostic commands

**Best for**:
- Something's not working
- Services fail to start
- Error messages
- Performance issues

---

## 🔧 System Requirements Summary

### Minimum
- **CPU**: 4 cores
- **RAM**: 16GB
- **Disk**: 20GB free
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- **Software**: Docker Desktop 20.10+

### Recommended
- **CPU**: 8+ cores
- **RAM**: 32GB
- **Disk**: 50GB SSD
- **GPU**: NVIDIA with 8GB+ VRAM (optional)
- **OS**: Latest versions

See [INSTALLATION.md](INSTALLATION.md) for detailed requirements.

---

## 🚀 Quick Reference

### Essential Commands

**Start services**:
```bash
docker compose -f docker/docker-compose.yml up -d
```

**Check status**:
```bash
docker compose ps
python scripts/admin/health_check.py
```

**View logs**:
```bash
docker compose logs -f
```

**Stop services**:
```bash
docker compose down
```

**Restart a service**:
```bash
docker compose restart <service_name>
```

### Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| n8n UI | http://localhost:5678 | Workflow automation |
| Weaviate | http://localhost:8080/v1/meta | Vector database info |

### Common Issues Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| Port conflict | Change port in `docker/.env` |
| Ollama desktop blocking | Quit Ollama app from system tray |
| Service unhealthy | `docker compose restart <service>` |
| Out of memory | Docker Desktop → Settings → Increase RAM |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

---

## 📖 Additional Resources

### Documentation
- **[API Reference](../api/README.md)** - Endpoint documentation
- **[Architecture Guide](../architecture/README.md)** - System design
- **[Usage Examples](../examples/README.md)** - Code examples
- **[Evaluation Guide](../evaluation/README.md)** - Quality monitoring

### Development
- **[CONTRIBUTING.md](../../CONTRIBUTING.md)** - Development setup
- **[Testing Guide](../../tests/TESTING.md)** - Running tests

### Project Info
- **[README.md](../../README.md)** - Project overview
- **[CHANGELOG.md](../../CHANGELOG.md)** - Version history
- **[ROADMAP.md](../../ROADMAP.md)** - Future plans

---

## ❓ Getting Help

**Can't find what you need?**

1. **Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Most common issues are covered
2. **Search [GitHub Issues](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues)** - Someone may have had the same problem
3. **Ask in [GitHub Discussions](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/discussions)** - Community help
4. **Open a [new issue](https://github.com/Jasonwts-x/BIS5151E_Research-Assistant/issues/new)** - Report bugs or request features

---

**[⬅ Back to Main README](../../README.md)**