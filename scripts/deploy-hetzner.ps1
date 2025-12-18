# Hetzner Deployment Script for Windows PowerShell
# Usage: .\deploy-hetzner.ps1
# Date: December 18, 2025

param(
    [string]$ServerIP = "46.224.66.48",
    [string]$User = "root",
    [string]$Password = "jvN9RqLbnqah3tta3KXv",
    [string]$PrimaryDomain = "shopfloor-copilot.com",
    [string]$SecondaryDomain = "opc-studio.com",
    [string]$Email = "admin@shopfloor-copilot.com"
)

$ErrorActionPreference = "Stop"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "HETZNER DEPLOYMENT SCRIPT" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server: $ServerIP" -ForegroundColor Yellow
Write-Host "Primary Domain: $PrimaryDomain" -ForegroundColor Yellow
Write-Host "Secondary Domain: $SecondaryDomain" -ForegroundColor Yellow
Write-Host ""

# Generate secure passwords
$PostgresPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
$SecretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 50 | ForEach-Object {[char]$_})

Write-Host "[OK] Generated secure passwords" -ForegroundColor Green

# Create temporary .env file
$envContent = @"
DATABASE_URL=postgresql://postgres:$PostgresPassword@postgres:5432/ragdb
POSTGRES_PASSWORD=$PostgresPassword
CHROMA_HOST=chroma
CHROMA_PORT=8000
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1:8b
SECRET_KEY=$SecretKey
API_BASE=http://localhost:8010/api
ENVIRONMENT=production
DEBUG=false
OPC_STUDIO_HTTP_PORT=8040
OPC_UA_PORT=4840
OPC_ENDPOINT=opc.tcp://0.0.0.0:4840/shopfloor/opc-studio
HISTORIAN_ENABLED=true
HISTORIAN_INTERVAL_S=5
ACTIVE_PLANT=TORINO
PRIMARY_DOMAIN=$PrimaryDomain
SECONDARY_DOMAIN=$SecondaryDomain
"@

$envContent | Out-File -FilePath ".env.prod" -Encoding utf8
Write-Host "[OK] Created production .env file" -ForegroundColor Green

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "MANUAL DEPLOYMENT STEPS" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Please follow these steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Connect to server:" -ForegroundColor White
Write-Host "   ssh root@$ServerIP" -ForegroundColor Gray
Write-Host "   Password: $Password" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Update system:" -ForegroundColor White
Write-Host "   apt-get update && apt-get upgrade -y" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Install Docker:" -ForegroundColor White
Write-Host "   curl -fsSL https://get.docker.com -o get-docker.sh" -ForegroundColor Gray
Write-Host "   sh get-docker.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Install dependencies:" -ForegroundColor White
Write-Host "   apt-get install -y git nginx certbot python3-certbot-nginx ufw fail2ban htop" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Configure firewall:" -ForegroundColor White
Write-Host "   ufw allow 22/tcp" -ForegroundColor Gray
Write-Host "   ufw allow 80/tcp" -ForegroundColor Gray
Write-Host "   ufw allow 443/tcp" -ForegroundColor Gray
Write-Host "   ufw --force enable" -ForegroundColor Gray
Write-Host ""
Write-Host "6. Create deployment directory:" -ForegroundColor White
Write-Host "   mkdir -p /opt/shopfloor" -ForegroundColor Gray
Write-Host "   cd /opt/shopfloor" -ForegroundColor Gray
Write-Host ""
Write-Host "7. Transfer files from your Windows machine:" -ForegroundColor White
Write-Host "   Use WinSCP or run from Windows:" -ForegroundColor Yellow
Write-Host "   scp -r * root@${ServerIP}:/opt/shopfloor/" -ForegroundColor Gray
Write-Host ""
Write-Host "8. On server, copy production files:" -ForegroundColor White
Write-Host "   cd /opt/shopfloor" -ForegroundColor Gray
Write-Host "   cp docker-compose.prod.yml docker-compose.yml" -ForegroundColor Gray
Write-Host "   cp .env.prod .env" -ForegroundColor Gray
Write-Host ""
Write-Host "9. Build and start services:" -ForegroundColor White
Write-Host "   docker compose build" -ForegroundColor Gray
Write-Host "   docker compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "10. Configure SSL (after DNS is pointing to server):" -ForegroundColor White
Write-Host "   certbot --nginx -d $PrimaryDomain -d www.$PrimaryDomain" -ForegroundColor Gray
Write-Host "   certbot --nginx -d $SecondaryDomain -d www.$SecondaryDomain" -ForegroundColor Gray
Write-Host ""
Write-Host "11. Configure Nginx reverse proxy:" -ForegroundColor White
Write-Host "   See nginx configuration in docs/HETZNER_DEPLOYMENT.md" -ForegroundColor Gray
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "AUTOMATED ALTERNATIVE" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Option 1: Use Git Bash on Windows:" -ForegroundColor Yellow
Write-Host "   Open Git Bash in this directory and run:" -ForegroundColor Gray
Write-Host "   ./scripts/hetzner-deploy.sh $ServerIP $PrimaryDomain $Email" -ForegroundColor Gray
Write-Host ""
Write-Host "Option 2: Use WSL (Windows Subsystem for Linux):" -ForegroundColor Yellow
Write-Host "   wsl" -ForegroundColor Gray
Write-Host "   cd /mnt/c/Users/Davide/VS-Code\ Solutions/rag-suite" -ForegroundColor Gray
Write-Host "   ./scripts/hetzner-deploy.sh $ServerIP $PrimaryDomain $Email" -ForegroundColor Gray
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "CREDENTIALS SAVED" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Database Password: $PostgresPassword" -ForegroundColor Green
Write-Host "Secret Key: $SecretKey" -ForegroundColor Green
Write-Host ""
Write-Host "These are saved in .env.prod file" -ForegroundColor Yellow
Write-Host ""
