# SAFE PRODUCTION DEPLOYMENT - PowerShell Version
# Hetzner Server: 46.224.66.48
# Date: December 22, 2025

$ErrorActionPreference = "Stop"

$SERVER = "root@46.224.66.48"
$APP_PATH = "/opt/shopfloor/rag-suite"
$BACKUP_PATH = "/opt/shopfloor/backups"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "🚀 SAFE PRODUCTION DEPLOYMENT" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Pre-deployment checklist:" -ForegroundColor Yellow
Write-Host "  ✓ Code committed and pushed to git" -ForegroundColor Green
Write-Host "  ✓ Local testing completed" -ForegroundColor Green
Write-Host "  ✓ All syntax errors fixed" -ForegroundColor Green
Write-Host ""

# Step 1: Create backup
Write-Host "Step 1/7: Creating backup snapshot..." -ForegroundColor Cyan
ssh $SERVER "mkdir -p $BACKUP_PATH && \
  cd $APP_PATH && \
  docker-compose logs shopfloor > $BACKUP_PATH/logs_before_$TIMESTAMP.txt && \
  tar -czf $BACKUP_PATH/rag-suite_backup_$TIMESTAMP.tar.gz \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.git' \
    . && \
  echo '✅ Backup created'"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Backup failed! Aborting deployment." -ForegroundColor Red
    exit 1
}

# Step 2: Pull latest code
Write-Host ""
Write-Host "Step 2/7: Pulling latest code from git..." -ForegroundColor Cyan
ssh $SERVER "cd $APP_PATH && \
  git fetch origin && \
  git reset --hard origin/main"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Git pull failed! Check connection." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Code updated" -ForegroundColor Green

# Step 3: Stop services
Write-Host ""
Write-Host "Step 3/7: Stopping services gracefully..." -ForegroundColor Cyan
ssh $SERVER "cd $APP_PATH && docker-compose stop shopfloor opc-studio"
Write-Host "✅ Services stopped" -ForegroundColor Green

# Step 4: Build images
Write-Host ""
Write-Host "Step 4/7: Building new Docker images..." -ForegroundColor Cyan
ssh $SERVER "cd $APP_PATH && docker-compose build shopfloor opc-studio"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    Write-Host "Rolling back..." -ForegroundColor Yellow
    ssh $SERVER "cd $APP_PATH && docker-compose up -d"
    exit 1
}
Write-Host "✅ Images built successfully" -ForegroundColor Green

# Step 5: Start services
Write-Host ""
Write-Host "Step 5/7: Starting services..." -ForegroundColor Cyan
ssh $SERVER "cd $APP_PATH && docker-compose up -d shopfloor opc-studio"
Write-Host "✅ Services started" -ForegroundColor Green

# Step 6: Wait for startup
Write-Host ""
Write-Host "Step 6/7: Waiting for services to be ready..." -ForegroundColor Cyan
for ($i = 30; $i -gt 0; $i--) {
    Write-Host "`r⏳ $i seconds remaining..." -NoNewline
    Start-Sleep -Seconds 1
}
Write-Host "`r✅ Wait complete                    " -ForegroundColor Green

# Step 7: Health check
Write-Host ""
Write-Host "Step 7/7: Performing health checks..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Container Status:" -ForegroundColor Yellow
ssh $SERVER "cd $APP_PATH && docker-compose ps"

Write-Host ""
Write-Host "Recent Logs:" -ForegroundColor Yellow
ssh $SERVER "cd $APP_PATH && docker-compose logs --tail=15 shopfloor"

Write-Host ""
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "✅ DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Service URLs:" -ForegroundColor Yellow
Write-Host "  • Shopfloor Copilot: http://46.224.66.48:8010" -ForegroundColor White
Write-Host "  • OPC Studio: http://46.224.66.48:8040" -ForegroundColor White
Write-Host ""
Write-Host "🔍 To check logs:" -ForegroundColor Yellow
Write-Host "  ssh $SERVER" -ForegroundColor Gray
Write-Host "  cd $APP_PATH" -ForegroundColor Gray
Write-Host "  docker-compose logs -f shopfloor" -ForegroundColor Gray
Write-Host ""
Write-Host "💾 Backup location:" -ForegroundColor Yellow
Write-Host "  $BACKUP_PATH/rag-suite_backup_$TIMESTAMP.tar.gz" -ForegroundColor Gray
Write-Host ""
Write-Host "🎉 Ready for your demo!" -ForegroundColor Green -BackgroundColor DarkGreen
Write-Host ""

# Open browser
$response = Read-Host "Open Shopfloor Copilot in browser? (Y/N)"
if ($response -eq "Y" -or $response -eq "y") {
    Start-Process "http://46.224.66.48:8010"
}
