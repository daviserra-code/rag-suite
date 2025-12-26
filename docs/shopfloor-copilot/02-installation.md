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

## Production Deployment to Hetzner (v0.3.1) 🆕

**Best Practice:** Deploy to dedicated cloud server for reliable 24/7 operation

### Production Server Specifications

**Hetzner Cloud Instance:**
- **IP:** 46.224.66.48
- **OS:** Ubuntu 22.04 LTS
- **CPU:** 4 vCPUs
- **RAM:** 16 GB
- **Storage:** 160 GB SSD
- **Network:** 20 TB traffic included
- **Location:** Falkenstein, Germany (eu-central)

**SSH Access:**
```bash
# Connect to server
ssh root@46.224.66.48

# Or use deploy script (Windows PowerShell)
.\deploy-production-safe.ps1
```

---

### Deployment Process

#### Step 1: Prepare Production Files

**On local machine:**

```powershell
# Windows PowerShell deployment script
# File: deploy-production-safe.ps1

# Define variables
$ServerIP = "46.224.66.48"
$RemoteUser = "root"
$RemotePath = "/root/rag-suite"

# 1. Build production Docker images locally
Write-Host "Building production images..." -ForegroundColor Green
docker-compose -f docker-compose.prod.yml build

# 2. Save images to tar files
Write-Host "Saving images..." -ForegroundColor Green
docker save -o shopfloor-image.tar rag-suite-shopfloor:latest
docker save -o opc-studio-image.tar rag-suite-opc-studio:latest

# 3. Upload files to server
Write-Host "Uploading to server..." -ForegroundColor Green
scp docker-compose.prod.yml ${RemoteUser}@${ServerIP}:${RemotePath}/
scp shopfloor-image.tar ${RemoteUser}@${ServerIP}:${RemotePath}/
scp opc-studio-image.tar ${RemoteUser}@${ServerIP}:${RemotePath}/
scp .env.production ${RemoteUser}@${ServerIP}:${RemotePath}/.env

# 4. SSH and deploy
Write-Host "Deploying on server..." -ForegroundColor Green
ssh ${RemoteUser}@${ServerIP} "cd ${RemotePath} && \
  docker load -i shopfloor-image.tar && \
  docker load -i opc-studio-image.tar && \
  docker-compose -f docker-compose.prod.yml down && \
  docker-compose -f docker-compose.prod.yml up -d && \
  rm *.tar"

# 5. Health check
Start-Sleep -Seconds 10
Write-Host "Checking health..." -ForegroundColor Green
$health = Invoke-WebRequest -Uri "http://46.224.66.48:8010/health" -UseBasicParsing
if ($health.StatusCode -eq 200) {
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
} else {
    Write-Host "❌ Health check failed!" -ForegroundColor Red
}
```

**Run deployment:**
```powershell
# Execute script
.\deploy-production-safe.ps1

# Or manual steps:
.\deploy-to-hetzner.ps1
```

---

#### Step 2: Configure Production Environment

**Create `.env.production` file:**

```env
# Production environment configuration
NODE_ENV=production

# Database (use external RDS/managed PostgreSQL in production)
POSTGRES_HOST=46.224.66.48
POSTGRES_PORT=5432
POSTGRES_USER=shopfloor_prod
POSTGRES_PASSWORD=<STRONG_PASSWORD_HERE>
POSTGRES_DB=shopfloor_mes

# Chroma (vector database)
CHROMA_HOST=46.224.66.48
CHROMA_PORT=8000

# Ollama (LLM service)
OLLAMA_BASE_URL=http://compassionate_thompson:11434
OLLAMA_MODEL=llama3.2

# Shopfloor Copilot
SHOPFLOOR_PORT=8010
LOG_LEVEL=INFO

# OPC Studio
OPC_STUDIO_PORT=8040
OPC_DEMO_ENDPOINT=opc.tcp://46.224.66.48:4850/freeopcua/server/

# Security (IMPORTANT!)
SECRET_KEY=<GENERATE_RANDOM_SECRET>
JWT_SECRET=<GENERATE_RANDOM_SECRET>
ALLOWED_ORIGINS=http://46.224.66.48:8010,https://yourdomain.com

# Monitoring
ENABLE_METRICS=true
SENTRY_DSN=<YOUR_SENTRY_DSN>  # Optional: error tracking
```

**Generate secrets:**
```bash
# Generate random secrets
openssl rand -hex 32
# Use output for SECRET_KEY and JWT_SECRET
```

---

#### Step 3: Production Docker Compose

**File:** `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always

  # ChromaDB (Vector Database)
  chroma:
    image: chromadb/chroma:latest
    environment:
      CHROMA_SERVER_HOST: 0.0.0.0
      CHROMA_SERVER_PORT: 8000
    volumes:
      - chroma_data:/chroma/data
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: always

  # OPC UA Demo Server
  opc-demo:
    build:
      context: ./opc-demo
      dockerfile: Dockerfile
    ports:
      - "4850:4850"
    healthcheck:
      test: ["CMD", "python", "-c", "import asyncua; print('OK')"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: always

  # OPC Studio (OPC UA abstraction layer)
  opc-studio:
    build:
      context: ./opc-studio
      dockerfile: Dockerfile.prod
    environment:
      OPC_DEMO_ENDPOINT: ${OPC_DEMO_ENDPOINT}
      LOG_LEVEL: ${LOG_LEVEL}
    ports:
      - "8040:8040"
    depends_on:
      - opc-demo
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8040/status"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: always

  # Shopfloor Copilot (Main UI)
  shopfloor:
    build:
      context: .
      dockerfile: Dockerfile.prod
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      CHROMA_HOST: chroma
      CHROMA_PORT: 8000
      OLLAMA_BASE_URL: ${OLLAMA_BASE_URL}
      OLLAMA_MODEL: ${OLLAMA_MODEL}
      SECRET_KEY: ${SECRET_KEY}
      ALLOWED_ORIGINS: ${ALLOWED_ORIGINS}
    ports:
      - "8010:8010"
    depends_on:
      - postgres
      - chroma
      - opc-studio
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8010/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: always
    volumes:
      - ./logs:/app/logs

volumes:
  postgres_data:
  chroma_data:
```

---

#### Step 4: Deploy to Server

**Execute deployment:**

```bash
# On production server (SSH)
cd /root/rag-suite

# Pull latest code
git pull origin main

# Load environment
source .env.production

# Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Check services
docker-compose -f docker-compose.prod.yml ps

# Expected output:
# NAME                  STATUS    PORTS
# rag-suite-postgres    Up        0.0.0.0:5432->5432/tcp
# rag-suite-chroma      Up        0.0.0.0:8000->8000/tcp
# rag-suite-opc-demo    Up        0.0.0.0:4850->4850/tcp
# rag-suite-opc-studio  Up        0.0.0.0:8040->8040/tcp
# rag-suite-shopfloor   Up        0.0.0.0:8010->8010/tcp
```

---

#### Step 5: Verify Deployment

**Health checks:**

```bash
# Check all services
curl http://46.224.66.48:8010/health
# Expected: {"status": "healthy", "version": "0.3.1"}

curl http://46.224.66.48:8040/status
# Expected: {"status": "ok", "opc_connected": true}

curl http://46.224.66.48:8000/api/v1/heartbeat
# Expected: {"status": "ok"}

# Check database connection
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U shopfloor_prod -d shopfloor_mes -c "SELECT NOW();"
# Expected: Current timestamp

# Check OPC connection
docker-compose -f docker-compose.prod.yml exec opc-studio \
  python -c "from asyncua import Client; print('OPC OK')"
# Expected: OPC OK
```

**Access UI:**
```
Open browser: http://46.224.66.48:8010
```

---

#### Step 6: Production Monitoring

**View logs:**

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f shopfloor

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 shopfloor

# Filter errors
docker-compose -f docker-compose.prod.yml logs | grep ERROR
```

**Container stats:**

```bash
# Resource usage
docker stats

# Expected:
# CONTAINER         CPU %   MEM USAGE / LIMIT   MEM %
# rag-suite-shopfloor   2.5%    1.2GiB / 16GiB      7.5%
# rag-suite-postgres    0.8%    512MiB / 16GiB      3.2%
# rag-suite-chroma      1.2%    800MiB / 16GiB      5.0%
```

**Health monitoring script:**

```bash
#!/bin/bash
# File: /root/rag-suite/health-check.sh

# Check all services
services=("8010" "8040" "8000")
for port in "${services[@]}"; do
  response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null || echo "000")
  if [ "$response" -eq 200 ]; then
    echo "✅ Port $port: OK"
  else
    echo "❌ Port $port: FAIL (HTTP $response)"
    # Send alert (email, Slack, PagerDuty, etc.)
  fi
done

# Run every 5 minutes
# Add to crontab: */5 * * * * /root/rag-suite/health-check.sh
```

---

### Production Troubleshooting

#### Problem: Deployment Fails with "Connection Refused"

**Cause:** Firewall blocking ports

**Solution:**
```bash
# Check firewall status
ufw status

# Allow required ports
ufw allow 8010/tcp  # Shopfloor UI
ufw allow 8040/tcp  # OPC Studio
ufw allow 4850/tcp  # OPC UA Server

# Enable firewall
ufw enable

# Verify
ufw status verbose
```

---

#### Problem: Docker Containers Keep Restarting

**Cause:** OOM (Out of Memory)

**Solution:**
```bash
# Check memory usage
free -h

# Check Docker logs for OOM
docker-compose -f docker-compose.prod.yml logs | grep "OOM"

# Add memory limits to docker-compose.prod.yml
services:
  shopfloor:
    mem_limit: 4g
    mem_reservation: 2g
```

---

#### Problem: Slow Performance

**Cause:** Insufficient resources or network latency

**Solution:**
```bash
# Check system load
uptime
# Load average should be < number of CPUs (4.0 for 4 vCPU)

# Check disk I/O
iostat -x 1 5

# Check network latency
ping 46.224.66.48

# Optimize database
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U shopfloor_prod -d shopfloor_mes -c "VACUUM ANALYZE;"

# Consider upgrading server plan
```

---

### Production Backup & Recovery

**Automated daily backup:**

```bash
#!/bin/bash
# File: /root/rag-suite/backup.sh

BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U shopfloor_prod shopfloor_mes | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# Backup ChromaDB
docker-compose -f docker-compose.prod.yml exec -T chroma \
  tar -czf - /chroma/data > $BACKUP_DIR/chroma_$DATE.tar.gz

# Backup configuration
cp .env.production $BACKUP_DIR/env_$DATE
cp docker-compose.prod.yml $BACKUP_DIR/docker-compose_$DATE.yml

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "✅ Backup completed: $DATE"
```

**Add to cron:**
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /root/rag-suite/backup.sh >> /var/log/backup.log 2>&1
```

**Restore from backup:**
```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore PostgreSQL
gunzip -c /root/backups/postgres_20251226_020000.sql.gz | \
  docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U shopfloor_prod -d shopfloor_mes

# Restore ChromaDB
docker-compose -f docker-compose.prod.yml exec -T chroma \
  tar -xzf - -C / < /root/backups/chroma_20251226_020000.tar.gz

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

---

### SSL/HTTPS Configuration (Optional)

**Using Let's Encrypt + Nginx:**

```bash
# Install Certbot
apt-get install certbot python3-certbot-nginx

# Get certificate (interactive)
certbot --nginx -d shopfloor.yourdomain.com

# Certificate auto-renews via cron
# Test renewal:
certbot renew --dry-run
```

**Nginx configuration:**
```nginx
# File: /etc/nginx/sites-available/shopfloor

server {
    listen 443 ssl http2;
    server_name shopfloor.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/shopfloor.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shopfloor.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name shopfloor.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

### Production Deployment Checklist ✅

**Pre-Deployment:**
- [ ] `.env.production` configured with strong passwords
- [ ] Secrets generated (SECRET_KEY, JWT_SECRET)
- [ ] SSL certificate obtained (if using HTTPS)
- [ ] Firewall configured (ports 8010, 8040, 4850 open)
- [ ] DNS configured (if using domain name)
- [ ] Backup script created and tested
- [ ] Health check script created

**Deployment:**
- [ ] Code pulled to server (git pull)
- [ ] Docker images built (docker-compose build)
- [ ] Services started (docker-compose up -d)
- [ ] Health checks passed (all endpoints return 200)
- [ ] UI accessible (http://46.224.66.48:8010)
- [ ] OPC connection verified
- [ ] Database connected
- [ ] RAG ingestion successful

**Post-Deployment:**
- [ ] Backups scheduled (cron job)
- [ ] Monitoring enabled (health-check.sh)
- [ ] Logs reviewed (no errors)
- [ ] Performance tested (acceptable response times)
- [ ] User access verified (operators can login)
- [ ] Documentation updated (README, runbooks)

---

**Deployment Scripts Location:**
- `deploy-production-safe.ps1` (Windows PowerShell)
- `deploy-production-safe.sh` (Linux Bash)
- `deploy-to-hetzner.ps1` (Direct SSH deployment)
- `hetzner-fix.sh` (Troubleshooting script)

See [CHANGELOG.md](CHANGELOG.md#deployment-to-hetzner) for detailed deployment notes from v0.3.1 release.

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
