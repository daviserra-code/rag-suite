# Hetzner Deployment Guide
## Shopfloor Copilot Production Deployment

**Target Platform:** Hetzner Cloud  
**System:** Shopfloor Copilot v0.3.0  
**Architecture:** Docker Compose → Kubernetes (future)  
**Last Updated:** December 18, 2025

---

## 📋 Table of Contents

1. [Infrastructure Planning](#infrastructure-planning)
2. [Server Provisioning](#server-provisioning)
3. [Network Configuration](#network-configuration)
4. [Security Hardening](#security-hardening)
5. [Deployment Automation](#deployment-automation)
6. [Database Setup](#database-setup)
7. [SSL/TLS Configuration](#ssltls-configuration)
8. [Monitoring & Alerting](#monitoring--alerting)
9. [Backup & Recovery](#backup--recovery)
10. [Scaling Strategy](#scaling-strategy)
11. [Cost Optimization](#cost-optimization)
12. [Troubleshooting](#troubleshooting)

---

## Infrastructure Planning

### Deployment Architecture Options

#### Option 1: Single Server (Small-Medium Plants)
**Best for:** 1-3 production lines, < 100 stations, pilot programs

```
┌─────────────────────────────────────────────┐
│  Hetzner Cloud Server (CX41)                │
│  ├─ Docker Compose Stack                    │
│  │  ├─ Shopfloor Copilot UI                 │
│  │  ├─ OPC Studio                           │
│  │  ├─ Core API                             │
│  │  ├─ PostgreSQL                           │
│  │  ├─ ChromaDB                             │
│  │  └─ Ollama (LLM)                         │
│  ├─ Nginx (Reverse Proxy + SSL)            │
│  └─ Monitoring (Prometheus + Grafana)       │
└─────────────────────────────────────────────┘
```

**Server Specs:**
- **Type:** CX41 (4 vCPU, 16 GB RAM, 160 GB SSD)
- **Cost:** ~€15/month
- **Capacity:** Up to 200 stations
- **Concurrent Users:** Up to 20

#### Option 2: Multi-Server (Large Plants)
**Best for:** 4+ production lines, > 100 stations, enterprise

```
┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
│  Load Balancer     │  │  Application       │  │  Database Server   │
│  (LB11)            │  │  Server (CX51)     │  │  (CPX41)           │
│  ├─ Nginx          │→ │  ├─ Shopfloor UI   │→ │  ├─ PostgreSQL     │
│  └─ SSL Termination│  │  ├─ OPC Studio     │  │  └─ Backups        │
└────────────────────┘  │  ├─ Core API       │  └────────────────────┘
                        │  └─ Ollama         │
                        └────────────────────┘  ┌────────────────────┐
                                                │  Storage Server    │
                        ┌────────────────────┐  │  (CX21)            │
                        │  Monitoring        │  │  ├─ ChromaDB       │
                        │  Server (CX21)     │  │  └─ Document Store │
                        │  ├─ Prometheus     │  └────────────────────┘
                        │  ├─ Grafana        │
                        │  └─ Alertmanager   │
                        └────────────────────┘
```

**Total Cost:** ~€60-80/month

#### Option 3: Hybrid (Cloud + On-Premise)
**Best for:** Regulated industries, data sovereignty requirements

```
┌─────────────────────────────────────────────────────────────┐
│  Hetzner Cloud (DMZ)                                        │
│  ├─ Shopfloor Copilot UI (public access)                   │
│  ├─ API Gateway (authenticated)                             │
│  └─ Static content, reports                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                   VPN Tunnel
                       │
┌──────────────────────┴──────────────────────────────────────┐
│  On-Premise (Factory Network)                               │
│  ├─ OPC Studio (direct PLC access)                          │
│  ├─ PostgreSQL (production data)                            │
│  └─ OPC UA Servers                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Server Provisioning

### Step 1: Create Hetzner Cloud Project

1. **Sign up:** https://console.hetzner.cloud/
2. **Create Project:** "shopfloor-prod"
3. **Generate API Token:**
   - Settings → API Tokens
   - Create token with Read & Write permissions
   - Save token securely

### Step 2: Choose Server Location

**Recommended Locations:**
- **Nuremberg (nbg1):** Germany, GDPR-compliant, low latency EU
- **Falkenstein (fsn1):** Germany, alternative datacenter
- **Helsinki (hel1):** Finland, good for Nordic/Eastern EU

**Selection Criteria:**
- Proximity to factory (< 50ms latency for OPC UA)
- Data residency requirements
- Backup location availability

### Step 3: Create Server via CLI

Install Hetzner CLI:
```bash
# Install hcloud CLI
wget https://github.com/hetznercloud/cli/releases/download/v1.42.0/hcloud-linux-amd64.tar.gz
tar -xzf hcloud-linux-amd64.tar.gz
sudo mv hcloud /usr/local/bin/
hcloud version

# Authenticate
hcloud context create shopfloor-prod
# Enter API token when prompted
```

Create server:
```bash
# Create SSH key
ssh-keygen -t ed25519 -C "shopfloor-deployment" -f ~/.ssh/shopfloor_deploy

# Add SSH key to Hetzner
hcloud ssh-key create --name shopfloor-deploy --public-key-from-file ~/.ssh/shopfloor_deploy.pub

# Create server
hcloud server create \
  --name shopfloor-prod-01 \
  --type cx41 \
  --image ubuntu-22.04 \
  --location nbg1 \
  --ssh-key shopfloor-deploy \
  --label environment=production \
  --label app=shopfloor-copilot

# Get server IP
hcloud server ip shopfloor-prod-01
```

### Step 4: Create Server via Web Console (Alternative)

1. Go to Hetzner Cloud Console
2. Click **"Add Server"**
3. **Location:** Nuremberg (nbg1)
4. **Image:** Ubuntu 22.04
5. **Type:** CX41 (4 vCPU, 16 GB RAM)
6. **Networking:**
   - IPv4: Enable
   - IPv6: Enable (optional)
7. **SSH Keys:** Add your public key
8. **Volumes:** None (using local SSD)
9. **Firewall:** Create new (see security section)
10. **Backups:** Enable (€3/month)
11. **Name:** shopfloor-prod-01
12. Click **"Create & Buy now"**

---

## Network Configuration

### Firewall Rules (Hetzner Cloud Firewall)

Create firewall via CLI:
```bash
# Create firewall
hcloud firewall create --name shopfloor-firewall

# Allow SSH (from your office IP only)
hcloud firewall add-rule shopfloor-firewall \
  --direction in \
  --port 22 \
  --protocol tcp \
  --source-ips YOUR_OFFICE_IP/32 \
  --description "SSH from office"

# Allow HTTP/HTTPS (from anywhere)
hcloud firewall add-rule shopfloor-firewall \
  --direction in \
  --port 80 \
  --protocol tcp \
  --source-ips 0.0.0.0/0 \
  --description "HTTP"

hcloud firewall add-rule shopfloor-firewall \
  --direction in \
  --port 443 \
  --protocol tcp \
  --source-ips 0.0.0.0/0 \
  --description "HTTPS"

# Allow OPC UA (from factory network only)
hcloud firewall add-rule shopfloor-firewall \
  --direction in \
  --port 4840 \
  --protocol tcp \
  --source-ips FACTORY_IP/32 \
  --description "OPC UA from factory"

# Apply firewall to server
hcloud firewall apply-to-resource shopfloor-firewall \
  --type server \
  --server shopfloor-prod-01
```

### Private Network (Optional - for multi-server)

```bash
# Create private network
hcloud network create \
  --name shopfloor-network \
  --ip-range 10.0.0.0/16

# Create subnet
hcloud network add-subnet shopfloor-network \
  --type cloud \
  --network-zone eu-central \
  --ip-range 10.0.1.0/24

# Attach server to network
hcloud server attach-to-network shopfloor-prod-01 \
  --network shopfloor-network \
  --ip 10.0.1.2
```

### DNS Configuration

**Option 1: Use Hetzner DNS (Free)**
```bash
# Add DNS zone
# Go to: https://dns.hetzner.com/
# Add domain: shopfloor.yourcompany.com
# Add A record: @ → SERVER_IP
# Add A record: www → SERVER_IP
```

**Option 2: Use Cloudflare (Recommended for DDoS protection)**
```bash
# Add domain to Cloudflare
# Update nameservers at domain registrar
# Add DNS records:
# A record: shopfloor.yourcompany.com → SERVER_IP
# Enable: Proxy status (orange cloud) for DDoS protection
```

---

## Security Hardening

### Step 1: Initial Server Setup

SSH into server:
```bash
ssh root@SERVER_IP
```

Update system:
```bash
# Update packages
apt update && apt upgrade -y

# Set timezone
timedatectl set-timezone Europe/Berlin

# Set hostname
hostnamectl set-hostname shopfloor-prod-01
```

### Step 2: Create Non-Root User

```bash
# Create deployment user
adduser deploy
usermod -aG sudo deploy

# Copy SSH keys
mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# Test login
# ssh deploy@SERVER_IP
```

### Step 3: Harden SSH

```bash
# Edit SSH config
nano /etc/ssh/sshd_config

# Apply these settings:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
X11Forwarding no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2

# Restart SSH
systemctl restart sshd
```

### Step 4: Configure UFW (Host-Level Firewall)

```bash
# Install UFW
apt install ufw -y

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (from office IP only)
ufw allow from YOUR_OFFICE_IP to any port 22 proto tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow OPC UA (from factory only)
ufw allow from FACTORY_IP to any port 4840 proto tcp

# Enable firewall
ufw enable

# Check status
ufw status verbose
```

### Step 5: Install Fail2Ban

```bash
# Install
apt install fail2ban -y

# Configure
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log
EOF

# Start service
systemctl enable fail2ban
systemctl start fail2ban

# Check status
fail2ban-client status sshd
```

### Step 6: Install and Configure Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Add deploy user to docker group
usermod -aG docker deploy

# Install Docker Compose
apt install docker-compose-plugin -y

# Verify
docker --version
docker compose version

# Configure Docker daemon
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true
}
EOF

systemctl restart docker
```

---

## Deployment Automation

### Step 1: Prepare Deployment Repository

On your local machine:
```bash
# Create deployment repository
mkdir shopfloor-deploy
cd shopfloor-deploy

# Initialize git
git init

# Create directory structure
mkdir -p config/{nginx,ssl,env}
mkdir -p scripts
mkdir -p backups

# Create .gitignore
cat > .gitignore << 'EOF'
.env
*.pem
*.key
backups/
logs/
*.log
EOF
```

### Step 2: Create Production Environment File

```bash
# Create production .env
cat > config/env/production.env << 'EOF'
# Database
POSTGRES_USER=shopfloor
POSTGRES_PASSWORD=CHANGE_THIS_SECURE_PASSWORD
POSTGRES_DB=shopfloor_mes
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Chroma
CHROMA_HOST=chroma
CHROMA_PORT=8000

# Ollama
OLLAMA_BASE_URL=http://ollama:11434

# OPC Studio
OPC_STUDIO_URL=http://opc-studio:8040

# Application
APP_ENV=production
LOG_LEVEL=INFO
SECRET_KEY=CHANGE_THIS_RANDOM_SECRET_KEY

# Security
ALLOWED_HOSTS=shopfloor.yourcompany.com,www.shopfloor.yourcompany.com
CORS_ORIGINS=https://shopfloor.yourcompany.com

# External OPC Server (your factory)
EXTERNAL_OPC_SERVER=opc.tcp://FACTORY_IP:4840
OPC_USERNAME=shopfloor_readonly
OPC_PASSWORD=CHANGE_THIS_OPC_PASSWORD
EOF

# Set secure permissions
chmod 600 config/env/production.env
```

### Step 3: Create Production Docker Compose

```bash
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: shopfloor-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./config/nginx/conf.d:/etc/nginx/conf.d:ro
      - ./config/ssl:/etc/nginx/ssl:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      - shopfloor
    networks:
      - shopfloor_net

  shopfloor:
    image: shopfloor-copilot:latest
    container_name: shopfloor-copilot
    restart: unless-stopped
    env_file:
      - config/env/production.env
    volumes:
      - shopfloor_data:/app/data
    depends_on:
      - postgres
      - chroma
      - ollama
    networks:
      - shopfloor_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8010/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  opc-studio:
    image: opc-studio:latest
    container_name: opc-studio
    restart: unless-stopped
    env_file:
      - config/env/production.env
    volumes:
      - ./opc-studio/config:/app/config:ro
      - opc_logs:/app/logs
    networks:
      - shopfloor_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8040/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    container_name: shopfloor-postgres
    restart: unless-stopped
    env_file:
      - config/env/production.env
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - shopfloor_net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U shopfloor"]
      interval: 10s
      timeout: 5s
      retries: 5

  chroma:
    image: chromadb/chroma:latest
    container_name: shopfloor-chroma
    restart: unless-stopped
    volumes:
      - chroma_data:/chroma/data
    networks:
      - shopfloor_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    container_name: shopfloor-ollama
    restart: unless-stopped
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - shopfloor_net
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  postgres_data:
  chroma_data:
  ollama_data:
  shopfloor_data:
  opc_logs:
  nginx_logs:

networks:
  shopfloor_net:
    driver: bridge
EOF
```

### Step 4: Create Deployment Script

```bash
cat > scripts/deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Deploying Shopfloor Copilot to Production..."

# Load environment
source config/env/production.env

# Pull latest images
echo "📦 Pulling latest images..."
docker compose -f docker-compose.prod.yml pull

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose -f docker-compose.prod.yml down

# Backup database before deployment
echo "💾 Backing up database..."
./scripts/backup.sh

# Start services
echo "▶️ Starting services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for health checks
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check health
echo "🏥 Health check..."
docker compose -f docker-compose.prod.yml ps

# Test endpoints
echo "🧪 Testing endpoints..."
curl -f http://localhost/health || echo "❌ Health check failed!"

echo "✅ Deployment complete!"
echo "🌐 Application available at: https://shopfloor.yourcompany.com"
EOF

chmod +x scripts/deploy.sh
```

### Step 5: Create Backup Script

```bash
cat > scripts/backup.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/home/deploy/shopfloor-deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "💾 Starting backup: $DATE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker exec shopfloor-postgres pg_dump -U shopfloor shopfloor_mes | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# Backup ChromaDB
echo "Backing up ChromaDB..."
docker exec shopfloor-chroma tar -czf /tmp/chroma_backup.tar.gz /chroma/data
docker cp shopfloor-chroma:/tmp/chroma_backup.tar.gz $BACKUP_DIR/chroma_$DATE.tar.gz

# Backup configuration
echo "Backing up configuration..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz config/

# Keep only last 7 days of backups
echo "Cleaning old backups..."
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "✅ Backup complete: $BACKUP_DIR"
echo "Files created:"
ls -lh $BACKUP_DIR/*_$DATE*
EOF

chmod +x scripts/backup.sh
```

---

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Free, Recommended)

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Obtain certificate
certbot --nginx -d shopfloor.yourcompany.com -d www.shopfloor.yourcompany.com

# Auto-renewal is configured automatically
# Test renewal:
certbot renew --dry-run
```

### Option 2: Manual Certificate

```bash
# Generate self-signed cert (dev/testing only)
mkdir -p config/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout config/ssl/server.key \
  -out config/ssl/server.crt \
  -subj "/C=DE/ST=Bavaria/L=Munich/O=YourCompany/CN=shopfloor.yourcompany.com"
```

### Nginx Configuration with SSL

```bash
cat > config/nginx/conf.d/shopfloor.conf << 'EOF'
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name shopfloor.yourcompany.com www.shopfloor.yourcompany.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name shopfloor.yourcompany.com www.shopfloor.yourcompany.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/shopfloor.yourcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shopfloor.yourcompany.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to Shopfloor Copilot
    location / {
        proxy_pass http://shopfloor:8010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for AI diagnostics
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://shopfloor:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check (no auth required)
    location /health {
        proxy_pass http://shopfloor:8010;
        access_log off;
    }
}
EOF
```

---

## Monitoring & Alerting

### Prometheus + Grafana Setup

```bash
# Create monitoring stack
cat > docker-compose.monitoring.yml << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    volumes:
      - ./config/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    ports:
      - "127.0.0.1:9090:9090"
    networks:
      - shopfloor_net

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=CHANGE_THIS_PASSWORD
      - GF_SERVER_ROOT_URL=https://shopfloor.yourcompany.com/grafana
    ports:
      - "127.0.0.1:3000:3000"
    networks:
      - shopfloor_net

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    command:
      - '--path.rootfs=/host'
    pid: host
    volumes:
      - '/:/host:ro,rslave'
    networks:
      - shopfloor_net

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    restart: unless-stopped
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    networks:
      - shopfloor_net

volumes:
  prometheus_data:
  grafana_data:

networks:
  shopfloor_net:
    external: true
EOF
```

### Prometheus Configuration

```bash
mkdir -p config/prometheus
cat > config/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'shopfloor'
    static_configs:
      - targets: ['shopfloor:8010']
    metrics_path: '/metrics'

  - job_name: 'opc-studio'
    static_configs:
      - targets: ['opc-studio:8040']
    metrics_path: '/metrics'
EOF
```

### Alert Rules

```bash
cat > config/prometheus/alerts.yml << 'EOF'
groups:
  - name: shopfloor_alerts
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          
      - alert: HighCPU
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          
      - alert: HighMemory
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
EOF
```

---

## Cost Optimization

### Hetzner Pricing (as of Dec 2025)

#### Single Server Setup
| Resource | Type | Specs | Monthly Cost |
|----------|------|-------|--------------|
| Server | CX41 | 4 vCPU, 16GB RAM | €15.30 |
| Backup | Automated | 7-day retention | €3.06 |
| Volume (optional) | 100 GB SSD | Extra storage | €5.00 |
| **Total** | | | **€23.36/month** |

#### Multi-Server Setup
| Resource | Type | Specs | Monthly Cost |
|----------|------|-------|--------------|
| App Server | CX51 | 8 vCPU, 32GB RAM | €30.09 |
| DB Server | CPX41 | 8 vCPU, 16GB RAM | €21.93 |
| Storage Server | CX21 | 2 vCPU, 4GB RAM | €5.23 |
| Monitoring | CX21 | 2 vCPU, 4GB RAM | €5.23 |
| Load Balancer | LB11 | 1 service | €5.39 |
| Backups | | For all servers | €12.55 |
| **Total** | | | **€80.42/month** |

### Cost Saving Tips

1. **Use Volumes for Large Data**
   - Volumes are cheaper than server storage
   - Can be detached and reattached
   - Good for PostgreSQL and ChromaDB

2. **Reserved Instances (Future)**
   - Hetzner doesn't offer reserved pricing yet
   - Monitor for announcements

3. **Downsize During Off-Hours**
   - Use smaller server type at night (via API)
   - Requires automation script

4. **Optimize Docker Images**
   - Use Alpine-based images
   - Multi-stage builds
   - Reduce layer count

5. **Use Object Storage for Backups**
   - Hetzner Storage Box: €3.81/month for 100GB
   - Cheaper than keeping backups on server

---

## Quick Start Deployment

### Complete Setup Script

```bash
cat > scripts/quick-deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Shopfloor Copilot - Quick Hetzner Deployment"
echo "================================================"

# Variables
SERVER_IP="YOUR_SERVER_IP"
DOMAIN="shopfloor.yourcompany.com"
EMAIL="admin@yourcompany.com"

echo "📋 Configuration:"
echo "   Server: $SERVER_IP"
echo "   Domain: $DOMAIN"
echo "   Email: $EMAIL"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 1; fi

# 1. Copy files to server
echo "📦 Copying files to server..."
scp -r ../rag-suite deploy@$SERVER_IP:/home/deploy/
scp docker-compose.prod.yml deploy@$SERVER_IP:/home/deploy/shopfloor-deploy/
scp -r config deploy@$SERVER_IP:/home/deploy/shopfloor-deploy/
scp -r scripts deploy@$SERVER_IP:/home/deploy/shopfloor-deploy/

# 2. SSH and setup
echo "🔧 Setting up server..."
ssh deploy@$SERVER_IP << 'ENDSSH'
cd /home/deploy/shopfloor-deploy

# Build images
docker build -t shopfloor-copilot:latest /home/deploy/rag-suite/apps/shopfloor_copilot/
docker build -t opc-studio:latest /home/deploy/rag-suite/opc-studio/

# Pull Ollama model
docker run --rm -v ollama_data:/root/.ollama ollama/ollama:latest ollama pull llama3.2

# Start services
docker compose -f docker-compose.prod.yml up -d

# Wait for services
sleep 30

# Initialize database
docker exec shopfloor-copilot python -m tools.init_mes_db

echo "✅ Server setup complete!"
ENDSSH

# 3. Configure SSL
echo "🔒 Configuring SSL..."
ssh deploy@$SERVER_IP "sudo certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --non-interactive"

# 4. Final checks
echo "🧪 Running health checks..."
sleep 10
curl -f https://$DOMAIN/health && echo "✅ Application is live!"

echo ""
echo "🎉 Deployment Complete!"
echo "🌐 Access: https://$DOMAIN"
echo "📊 Monitoring: https://$DOMAIN/grafana"
echo ""
echo "Next steps:"
echo "1. Configure OPC connection to your factory"
echo "2. Upload work instructions to RAG"
echo "3. Customize semantic mappings"
echo "4. Train operators"
EOF

chmod +x scripts/quick-deploy.sh
```

---

## Maintenance Procedures

### Daily Tasks (Automated)
- Backup database (cron: 2 AM)
- Rotate logs
- Health check alerts

### Weekly Tasks
- Review monitoring dashboards
- Check disk space
- Review security logs
- Update Docker images (if available)

### Monthly Tasks
- Security updates (apt upgrade)
- Review backup integrity
- Cost analysis
- Performance optimization review

### Cron Jobs

```bash
# Add to /etc/crontab
0 2 * * * deploy /home/deploy/shopfloor-deploy/scripts/backup.sh
0 3 * * 0 deploy docker system prune -af --volumes
0 4 * * * deploy /home/deploy/shopfloor-deploy/scripts/health-check.sh
```

---

## Next Steps

1. **Review and customize** all configuration files
2. **Update passwords** and secrets in production.env
3. **Configure DNS** to point to your Hetzner server
4. **Run deployment script**
5. **Configure monitoring alerts**
6. **Test backup/restore procedures**
7. **Document runbook** for your team

---

**Deployment Checklist:**
- [ ] Hetzner account created
- [ ] Server provisioned
- [ ] Firewall configured
- [ ] DNS configured
- [ ] SSL certificate obtained
- [ ] Production environment variables set
- [ ] Docker images built
- [ ] Services deployed
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Team trained on runbook

**Estimated Setup Time:** 2-4 hours (first time)

**Monthly Cost:** €23-80 depending on configuration

**Support:** For issues, check logs with `docker compose -f docker-compose.prod.yml logs -f`
