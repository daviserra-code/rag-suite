# Service Initialization Scripts

These scripts automatically configure OPC Studio and load semantic mappings after Docker containers start.

## Quick Start

### Windows (PowerShell)
```powershell
# Start containers
docker compose up -d

# Wait 30 seconds for services to start
Start-Sleep -Seconds 30

# Run initialization
powershell -ExecutionPolicy Bypass -File .\scripts\init-services.ps1
```

### Linux/macOS (Bash)
```bash
# Start containers
docker compose up -d

# Wait 30 seconds
sleep 30

# Run initialization
chmod +x scripts/init-services.sh
./scripts/init-services.sh
```

## What Gets Configured

1. **✓ OPC Studio Connection**
   - Connects to OPC demo server at `opc.tcp://opc-demo:4850`
   - Enables OPC UA browsing and data reading
   
2. **✓ Semantic Mappings**
   - Loads `opc-studio/config/semantic_mappings.yaml`
   - Maps raw OPC tags to semantic MES signals
   - Enables loss category classification

3. **✓ Service Health Checks**
   - Waits for all services to be ready
   - Verifies semantic snapshot availability
   - Tests OPC browse functionality

4. **✓ Ollama Model Check**
   - Verifies LLM model is installed
   - Recommends `llama3.2:3b` if missing

5. **✓ PostgreSQL Client Check**
   - Detects if `psql` is installed (optional)
   - Provides installation instructions

## Manual Configuration

If you prefer to configure services manually:

### 1. Connect OPC Studio
```powershell
# PowerShell
$body = '{"endpoint":"opc.tcp://opc-demo:4850"}'
Invoke-RestMethod -Uri "http://localhost:8040/opc/connect" -Method Post -Body $body -ContentType "application/json"
```

```bash
# Bash
curl -X POST http://localhost:8040/opc/connect \
  -H "Content-Type: application/json" \
  -d '{"endpoint":"opc.tcp://opc-demo:4850"}'
```

### 2. Load Semantic Mappings
```powershell
# PowerShell
$body = '{"yaml_path":"config/semantic_mappings.yaml"}'
Invoke-RestMethod -Uri "http://localhost:8040/mapping/load" -Method Post -Body $body -ContentType "application/json"
```

```bash
# Bash
curl -X POST http://localhost:8040/mapping/load \
  -H "Content-Type: application/json" \
  -d '{"yaml_path":"config/semantic_mappings.yaml"}'
```

### 3. Verify Configuration
```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8040/semantic/snapshot"
```

```bash
# Bash
curl http://localhost:8040/semantic/snapshot | jq
```

## Troubleshooting

### OPC Connection Fails
**Problem:** `Failed to connect to OPC server`

**Solution:**
```bash
# Check if OPC demo server is running
docker compose ps opc-demo

# Check logs
docker compose logs opc-demo

# Restart if needed
docker compose restart opc-demo
```

### Semantic Mappings Fail to Load
**Problem:** `Failed to load semantic mappings`

**Solution:**
```bash
# Verify YAML file exists
ls opc-studio/config/semantic_mappings.yaml

# Check OPC Studio logs
docker compose logs opc-studio

# Restart OPC Studio
docker compose restart opc-studio
```

### Ollama Model Missing
**Problem:** `No Llama models found in Ollama`

**Solution:**
```bash
# Pull the recommended model (2GB download)
docker exec shopfloor-ollama ollama pull llama3.2:3b

# Verify installation
docker exec shopfloor-ollama ollama list
```

### Script Hangs or Times Out
**Problem:** Script waits indefinitely

**Solution:**
```bash
# Check all containers are running
docker compose ps

# Look for unhealthy containers
docker compose ps --filter "health=unhealthy"

# Check logs for specific service
docker compose logs <service-name>

# Restart all services
docker compose restart
```

## Integration with Docker Compose

To auto-initialize services on startup, add to `docker-compose.yml`:

```yaml
services:
  init-helper:
    image: curlimages/curl:latest
    depends_on:
      - opc-studio
      - shopfloor
    command: >
      sh -c "
        sleep 30 &&
        curl -X POST http://opc-studio:8040/opc/connect 
          -H 'Content-Type: application/json' 
          -d '{\"endpoint\":\"opc.tcp://opc-demo:4850\"}' &&
        curl -X POST http://opc-studio:8040/mapping/load 
          -H 'Content-Type: application/json' 
          -d '{\"yaml_path\":\"config/semantic_mappings.yaml\"}'
      "
    restart: "no"
```

## After Initialization

Once services are initialized, run smoke tests to verify:

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .\scripts\SMOKE_TEST.ps1
```

```bash
# Linux/macOS
./scripts/SMOKE_TEST.sh
```

Expected result: **PASS: 10+, FAIL: 0, WARN: 0-2**

---

**Version:** 1.0  
**Last Updated:** December 21, 2025
