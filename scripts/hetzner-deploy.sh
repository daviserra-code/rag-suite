#!/bin/bash
# Hetzner Automated Deployment Script
# Usage: ./hetzner-deploy.sh SERVER_IP DOMAIN [EMAIL]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVER_IP="${1}"
DOMAIN="${2}"
EMAIL="${3:-admin@${DOMAIN}}"
DEPLOY_USER="deploy"

if [ -z "$SERVER_IP" ] || [ -z "$DOMAIN" ]; then
    echo -e "${RED}Usage: $0 SERVER_IP DOMAIN [EMAIL]${NC}"
    echo "Example: $0 123.45.67.89 shopfloor.example.com admin@example.com"
    exit 1
fi

echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Shopfloor Copilot - Hetzner Deployment Script      ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Server IP: $SERVER_IP"
echo "  Domain: $DOMAIN"
echo "  Email: $EMAIL"
echo "  Deploy User: $DEPLOY_USER"
echo ""
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Deployment cancelled${NC}"
    exit 1
fi

# Function to run command via SSH
ssh_cmd() {
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${DEPLOY_USER}@${SERVER_IP} "$1"
}

# Function to check if command succeeded
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1 failed${NC}"
        exit 1
    fi
}

echo ""
echo -e "${YELLOW}[1/10] Testing SSH connection...${NC}"
ssh_cmd "echo 'SSH connection successful'" > /dev/null 2>&1
check_success "SSH connection established"

echo ""
echo -e "${YELLOW}[2/10] Updating system packages...${NC}"
ssh_cmd "sudo apt update && sudo DEBIAN_FRONTEND=noninteractive apt upgrade -y" > /dev/null 2>&1
check_success "System packages updated"

echo ""
echo -e "${YELLOW}[3/10] Installing Docker...${NC}"
ssh_cmd "curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker ${DEPLOY_USER}" > /dev/null 2>&1
check_success "Docker installed"

echo ""
echo -e "${YELLOW}[4/10] Installing dependencies...${NC}"
ssh_cmd "sudo apt install -y git nginx certbot python3-certbot-nginx ufw fail2ban htop" > /dev/null 2>&1
check_success "Dependencies installed"

echo ""
echo -e "${YELLOW}[5/10] Configuring firewall...${NC}"
ssh_cmd "
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw --force enable
" > /dev/null 2>&1
check_success "Firewall configured"

echo ""
echo -e "${YELLOW}[6/10] Creating deployment directory...${NC}"
ssh_cmd "mkdir -p /home/${DEPLOY_USER}/shopfloor-deploy/{config/{nginx/conf.d,ssl,env},scripts,backups}"
check_success "Deployment directory created"

echo ""
echo -e "${YELLOW}[7/10] Copying project files...${NC}"
# Create a temporary archive
echo "  Creating archive..."
tar czf /tmp/shopfloor-deploy.tar.gz \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    -C .. rag-suite

echo "  Uploading to server..."
scp -o StrictHostKeyChecking=no /tmp/shopfloor-deploy.tar.gz ${DEPLOY_USER}@${SERVER_IP}:/tmp/
ssh_cmd "cd /home/${DEPLOY_USER} && tar xzf /tmp/shopfloor-deploy.tar.gz && rm /tmp/shopfloor-deploy.tar.gz"
rm /tmp/shopfloor-deploy.tar.gz
check_success "Project files copied"

echo ""
echo -e "${YELLOW}[8/10] Creating production environment file...${NC}"
# Generate secure passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)

ssh_cmd "cat > /home/${DEPLOY_USER}/shopfloor-deploy/config/env/production.env << 'EOF'
# Database
POSTGRES_USER=shopfloor
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
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
SECRET_KEY=${SECRET_KEY}

# Security
ALLOWED_HOSTS=${DOMAIN},www.${DOMAIN}
CORS_ORIGINS=https://${DOMAIN}

# External OPC Server (configure after deployment)
# EXTERNAL_OPC_SERVER=opc.tcp://YOUR_FACTORY_IP:4840
# OPC_USERNAME=shopfloor_readonly
# OPC_PASSWORD=CHANGE_THIS
EOF"
check_success "Environment file created"

echo ""
echo -e "${YELLOW}[9/10] Building Docker images...${NC}"
echo "  This may take 5-10 minutes..."
ssh_cmd "
cd /home/${DEPLOY_USER}/rag-suite
docker compose build
" 
check_success "Docker images built"

echo ""
echo -e "${YELLOW}[10/10] Starting services...${NC}"
ssh_cmd "
cd /home/${DEPLOY_USER}/rag-suite
docker compose up -d
sleep 30
docker compose ps
"
check_success "Services started"

echo ""
echo -e "${YELLOW}[BONUS] Configuring SSL with Let's Encrypt...${NC}"
ssh_cmd "
sudo certbot --nginx -d ${DOMAIN} --email ${EMAIL} --agree-tos --non-interactive --redirect
" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ SSL certificate installed${NC}"
    PROTOCOL="https"
else
    echo -e "${YELLOW}⚠ SSL configuration failed (can be done manually later)${NC}"
    PROTOCOL="http"
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Deployment Successful! 🎉                 ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}🌐 Application URL:${NC} ${PROTOCOL}://${DOMAIN}"
echo -e "${GREEN}📊 Server IP:${NC} ${SERVER_IP}"
echo -e "${GREEN}🔐 Deploy User:${NC} ${DEPLOY_USER}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Configure DNS A record: ${DOMAIN} → ${SERVER_IP}"
echo "2. SSH to server: ssh ${DEPLOY_USER}@${SERVER_IP}"
echo "3. Configure OPC connection in: config/env/production.env"
echo "4. Upload work instructions for RAG"
echo "5. Customize semantic mappings"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo "  View logs: docker compose logs -f shopfloor"
echo "  Restart: docker compose restart shopfloor"
echo "  Backup: ./scripts/backup.sh"
echo ""
echo -e "${GREEN}Credentials saved to: /home/${DEPLOY_USER}/shopfloor-deploy/config/env/production.env${NC}"
echo ""
