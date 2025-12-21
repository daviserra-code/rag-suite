# Ollama Configuration Strategy

## Problem
Local dev machine (AMD GPU, 128GB RAM) was too slow with Docker Ollama due to WSL2 overhead and resource limits.

## Solution
**Environment-specific Ollama configuration:**

### Local Development (Windows + AMD)
- **Native Ollama** with AMD optimization: `C:\Program Files\AIPC\resources\runtime\ollama\brand\amd\ollama.exe`
- Docker Ollama container: **STOPPED** (using profile exclusion)
- Connection: `host.docker.internal:11434`
- Performance: **Native speed with full hardware access**

### Hetzner Production (Linux)
- **Docker Ollama** container (standard image)
- Connection: `http://ollama:11434`
- Start with: `docker compose --profile hetzner up -d`

---

## Deployment Process

### 1. Local Development (Current Setup)
```powershell
# Use .env with host.docker.internal
cp .env.local .env

# Start services WITHOUT Ollama container
docker compose up -d

# Native Ollama runs automatically (Windows service)
```

### 2. Hetzner Deployment
```bash
# SSH to Hetzner
ssh root@46.224.66.48

# Navigate to project
cd /opt/shopfloor/rag-suite

# Pull latest code
git pull

# Use Hetzner environment config
cp .env.hetzner .env

# Start ALL services including Ollama
docker compose --profile hetzner up -d

# Pull model into Docker Ollama
docker exec shopfloor-ollama ollama pull llama3.2:3b

# Verify
docker compose --profile hetzner ps
curl http://localhost:11434/api/tags
```

---

## Configuration Files

| File | Environment | OLLAMA_BASE_URL |
|------|-------------|-----------------|
| `.env.local` | Local dev | `http://host.docker.internal:11434` |
| `.env.hetzner` | Production | `http://ollama:11434` |
| `.env` | Active (gitignored) | Changes per environment |

---

## Benefits

✅ **Local**: Native AMD Ollama = Fast LLM responses  
✅ **Hetzner**: Self-contained Docker stack = Easy deployment  
✅ **No code changes**: Only `.env` differs between environments  
✅ **Backward compatible**: `host.docker.internal` harmless on Linux  

---

## Testing

### Local
```powershell
# Test native Ollama
& "C:\Program Files\AIPC\resources\runtime\ollama\brand\amd\ollama.exe" run llama3.2:3b "Hello"

# Test diagnostics API
.\scripts\SMOKE_TEST.ps1
```

### Hetzner
```bash
# Test Docker Ollama
docker exec shopfloor-ollama ollama run llama3.2:3b "Hello"

# Test diagnostics API
./scripts/SMOKE_TEST.sh
```

---

## Rollback

If issues on Hetzner, fall back to local Docker Ollama:
```bash
# Stop profile-based Ollama
docker compose --profile hetzner down ollama

# Start regular Ollama (remove profile from docker-compose.yml)
docker compose up -d ollama
```
