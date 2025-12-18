# Chapter 2: Installation & Setup

## Prerequisites

### System Requirements

**Server/Host Machine:**
- **OS:** Linux (Ubuntu 20.04+), Windows 10+ with WSL2, or macOS 11+
- **CPU:** 4 cores minimum (8 cores recommended for production)
- **RAM:** 8 GB minimum (16 GB recommended)
- **Storage:** 50 GB minimum (100 GB recommended for production)
- **Network:** 1 Gbps LAN connection

**Client/Browser:**
- **Browser:** Chrome 90+, Firefox 88+, Edge 90+, Safari 14+
- **Screen Resolution:** 1920x1080 minimum (1920x1200 recommended)
- **Network:** 10 Mbps minimum connection to server

### Required Software

1. **Docker Engine 24.0+**
2. **Docker Compose 2.20+**
3. **Git** (for cloning repository)

---

## Installation Steps

### Step 1: Install Docker

#### On Ubuntu/Debian
```bash
# Update package index
sudo apt-get update

# Install dependencies
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

#### On Windows
1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop
2. Run installer
3. Enable WSL2 integration during setup
4. Restart computer
5. Verify:
   ```powershell
   docker --version
   docker compose version
   ```

#### On macOS
1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop
2. Drag to Applications folder
3. Open Docker.app
4. Verify:
   ```bash
   docker --version
   docker compose version
   ```

### Step 2: Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-org/rag-suite.git
cd rag-suite

# Verify contents
ls -la
# Should see: docker-compose.yml, apps/, packages/, opc-studio/, etc.
```

### Step 3: Install Ollama (LLM Service)

Ollama is required for AI Diagnostics (Sprint 3).

#### On Linux
```bash
# Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve &

# Pull llama3.2 model
ollama pull llama3.2

# Verify
ollama list
# Should show: llama3.2:latest
```

#### On Windows/macOS
1. Download Ollama from: https://ollama.com/download
2. Install and run
3. Open terminal:
   ```bash
   ollama pull llama3.2
   ollama list
   ```

#### Note Ollama Container Name
```bash
# Find Ollama container name
docker ps | grep ollama

# Output example:
# 4788087b5edf   ollama/ollama:latest   "/bin/ollama serve"   compassionate_thompson

# Note the name: compassionate_thompson (or your container name)
```

### Step 4: Configure Environment

Create `.env` file in project root:

```bash
cd rag-suite
nano .env
```

Add configuration:

```env
# Database
POSTGRES_USER=shopfloor
POSTGRES_PASSWORD=your-secure-password-here
POSTGRES_DB=shopfloor_mes

# Chroma
CHROMA_HOST=chroma
CHROMA_PORT=8000

# Ollama (update with your container name)
OLLAMA_BASE_URL=http://compassionate_thompson:11434

# OPC Studio
OPC_STUDIO_URL=http://opc-studio:8040

# API Keys (optional)
# OPENAI_API_KEY=sk-...
```

**Security Note:** Replace `your-secure-password-here` with a strong password!

### Step 5: Build and Start Services

```bash
# Build all services
docker-compose build

# Start services in background
docker-compose up -d

# Verify all services are running
docker-compose ps

# Expected output:
# NAME                     STATUS              PORTS
# rag-suite-api-1          Up                 0.0.0.0:8000->8000/tcp
# rag-suite-shopfloor-1    Up                 0.0.0.0:8010->8010/tcp
# rag-suite-opc-studio-1   Up                 0.0.0.0:8040->8040/tcp
# rag-suite-opc-demo-1     Up                 0.0.0.0:4850->4850/tcp
# rag-suite-chroma-1       Up                 0.0.0.0:8001->8000/tcp
# rag-suite-postgres-1     Up                 0.0.0.0:5432->5432/tcp
```

### Step 6: Initialize Database

```bash
# Run database migrations
docker-compose exec api python -m tools.init_mes_db

# Verify tables created
docker-compose exec postgres psql -U shopfloor -d shopfloor_mes -c "\dt"

# Expected output:
# Schema |       Name        | Type  |   Owner
# -------+-------------------+-------+-----------
# public | production_lines  | table | shopfloor
# public | shift_records     | table | shopfloor
# public | oee_data          | table | shopfloor
```

### Step 7: Load Sample Data

```bash
# Import production lines
docker-compose exec api python -m tools.import_oee_data

# Simulate historical data
docker-compose exec api python simulate_plant_history.py

# Verify data
docker-compose exec postgres psql -U shopfloor -d shopfloor_mes -c "SELECT COUNT(*) FROM shift_records;"

# Expected: 2970 rows (or similar)
```

### Step 8: Populate RAG Knowledge Base

```bash
# Ingest sample documents (if available)
docker-compose exec api python ingest_documents.py

# Or use API
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "sample_docs/work_instructions/",
    "doc_type": "work_instruction"
  }'

# Verify ChromaDB collection
curl http://localhost:8001/api/v1/collections | jq
```

### Step 9: Verify Installation

Run health checks:

```bash
# Core API
curl http://localhost:8000/health
# Expected: {"status": "ok", "app": "core_api"}

# Shopfloor Copilot
curl http://localhost:8010/health
# Expected: {"status": "ok", "app": "shopfloor_copilot"}

# OPC Studio
curl http://localhost:8040/health
# Expected: {"ok": true, "service": "opc_studio"}

# OPC Demo Server (should be running)
curl http://localhost:8040/status
# Expected: {"connected": true, "server": "opc.tcp://opc-demo:4850"}

# AI Diagnostics
curl http://localhost:8010/api/diagnostics/health
# Expected: {"ok": true, "service": "diagnostics"}

# ChromaDB
curl http://localhost:8001/api/v1
# Expected: {"nanosecond heartbeat": ...}
```

### Step 10: Access UI

Open browser and navigate to:

**Shopfloor Copilot:** http://localhost:8010

You should see the main UI with 23 tabs.

---

## Post-Installation Configuration

### Configure OPC Connection (If Using External Server)

If not using the demo server:

1. Navigate to **Tab 15: OPC Explorer**
2. Enter your OPC server URL: `opc.tcp://your-server:4840`
3. Click **Connect**
4. If authentication required, enter credentials

### Configure Semantic Mappings

To add your station types:

1. Edit `opc-studio/config/semantic_mappings.yaml`
2. Add new station type under `station_types:`
3. Define signals and loss category mappings
4. Restart OPC Studio:
   ```bash
   docker-compose restart opc-studio
   ```

### Add Work Instructions to RAG

Place your documents in `docs/work_instructions/`:

```bash
# Create directory structure
mkdir -p docs/work_instructions
mkdir -p docs/sop
mkdir -p docs/maintenance_logs

# Copy your documents
cp /path/to/WI-*.pdf docs/work_instructions/

# Ingest documents
docker-compose exec api python ingest_documents.py \
  --source docs/work_instructions \
  --doc-type work_instruction
```

---

## Troubleshooting Installation

### Problem: Docker Compose Not Found

**Error:**
```
docker-compose: command not found
```

**Solution (Linux):**
```bash
# Install docker-compose-plugin
sudo apt-get install docker-compose-plugin

# Use: docker compose (with space, not hyphen)
docker compose up -d
```

### Problem: Permission Denied

**Error:**
```
Got permission denied while trying to connect to the Docker daemon
```

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and log back in
# Or run:
newgrp docker

# Verify
docker ps
```

### Problem: Port Already in Use

**Error:**
```
Bind for 0.0.0.0:8010 failed: port is already allocated
```

**Solution:**
```bash
# Find process using port
sudo lsof -i :8010

# Kill process or stop conflicting container
docker stop <container-name>

# Or change port in docker-compose.yml
ports:
  - "8011:8010"  # Use 8011 instead
```

### Problem: Ollama Not Found

**Error:**
```
ERROR: [Errno -2] Name or service not known
```

**Solution:**
```bash
# Verify Ollama is running
docker ps | grep ollama

# Update .env with correct container name
OLLAMA_BASE_URL=http://<your-ollama-container-name>:11434

# Restart services
docker-compose restart shopfloor
```

### Problem: Database Connection Failed

**Error:**
```
could not connect to server: Connection refused
```

**Solution:**
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Wait 10 seconds for startup
sleep 10

# Verify connection
docker-compose exec postgres psql -U shopfloor -d shopfloor_mes -c "SELECT 1;"
```

### Problem: OPC Demo Server Not Starting

**Error:**
```
OPC UA Server failed to start
```

**Solution:**
```bash
# Check logs
docker-compose logs opc-demo

# Common issue: Port 4850 in use
sudo lsof -i :4850

# Restart demo server
docker-compose restart opc-demo

# Check startup logs
docker-compose logs -f opc-demo
# Should see: "OPC UA Server started"
```

---

## Updating the System

### Pulling Latest Changes

```bash
# Stop services
docker-compose down

# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Start services
docker-compose up -d

# Check for migrations
docker-compose exec api python -m tools.check_migrations
```

### Updating Ollama Model

```bash
# Pull latest llama3.2
ollama pull llama3.2

# Restart diagnostics service
docker-compose restart shopfloor
```

### Backup Before Update

```bash
# Backup database
docker-compose exec postgres pg_dump -U shopfloor shopfloor_mes > backup_$(date +%Y%m%d).sql

# Backup ChromaDB
docker-compose exec chroma tar -czf /tmp/chroma_backup.tar.gz /chroma/data
docker cp rag-suite-chroma-1:/tmp/chroma_backup.tar.gz ./chroma_backup_$(date +%Y%m%d).tar.gz

# Backup configuration
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup
```

---

## Uninstalling

### Stop and Remove Services

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Clean up Docker system
docker system prune -a
```

### Remove Project

```bash
cd ..
rm -rf rag-suite
```

---

## Production Deployment

### Recommended Changes for Production

1. **Use Environment Secrets:**
   ```bash
   # Store sensitive data in Docker secrets
   docker secret create postgres_password /path/to/password.txt
   ```

2. **Enable HTTPS:**
   ```yaml
   # Add nginx reverse proxy
   services:
     nginx:
       image: nginx:alpine
       ports:
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf
         - ./certs:/etc/nginx/certs
   ```

3. **Use External Database:**
   ```env
   # .env
   POSTGRES_HOST=your-db-server.com
   POSTGRES_PORT=5432
   ```

4. **Enable Authentication:**
   - Configure OAuth/SAML for Shopfloor UI
   - Implement API key authentication
   - Set up RBAC for operators vs managers

5. **Set Up Monitoring:**
   ```bash
   # Add Prometheus + Grafana
   docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
   ```

6. **Configure Backups:**
   ```bash
   # Add cron job for daily backups
   0 2 * * * /opt/rag-suite/backup.sh
   ```

---

**Next Chapter:** [Quick Start Guide →](03-quick-start.md)

**Previous Chapter:** [← Introduction & Overview](01-introduction.md)
