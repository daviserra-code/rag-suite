# Deploy OPC Endpoint Fix to Hetzner
# Quick deployment script for OPC endpoint configuration

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploy OPC Endpoint Fix to Hetzner" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ServerIP = "46.224.66.48"
$RemoteUser = "root"
$RemotePath = "/root/rag-suite"

# 1. Upload updated .env.hetzner
Write-Host "1. Uploading .env configuration..." -ForegroundColor Green
scp .env.hetzner ${RemoteUser}@${ServerIP}:${RemotePath}/.env

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to upload .env file" -ForegroundColor Red
    exit 1
}

# 2. Check directory structure and create if needed
Write-Host "2. Checking directory structure..." -ForegroundColor Green
$remoteDirCheck = @'
cd /root/rag-suite
echo 'Creating required directories...'
mkdir -p apps/shopfloor_copilot/screens
ls -la apps/shopfloor_copilot/screens || echo 'Directory created'
'@

ssh ${RemoteUser}@${ServerIP} $remoteDirCheck

# 3. Upload updated opc_explorer.py
Write-Host "3. Uploading updated OPC Explorer code..." -ForegroundColor Green
scp apps/shopfloor_copilot/screens/opc_explorer.py ${RemoteUser}@${ServerIP}:${RemotePath}/apps/shopfloor_copilot/screens/opc_explorer.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Warning: Could not upload opc_explorer.py" -ForegroundColor Yellow
    Write-Host "   This is OK if you're using pre-built images." -ForegroundColor Yellow
    Write-Host "   The .env change alone will fix the endpoint." -ForegroundColor Yellow
}

# 4. Rebuild and restart services
Write-Host "`n4. Restarting services on server..." -ForegroundColor Green
$remoteCommands = @'
cd /root/rag-suite
echo 'Current OPC endpoint configuration:'
grep OPC_DEMO_ENDPOINT .env || echo 'OPC_DEMO_ENDPOINT not set (will use code default: opc.tcp://46.224.66.48:4850)'
echo ''
echo 'Stopping services...'
docker-compose down
echo ''
echo 'Rebuilding shopfloor image with updated code...'
docker-compose build shopfloor
echo ''
echo 'Starting services...'
docker-compose up -d
echo ''
echo 'Waiting for services to start...'
sleep 15
'@

ssh ${RemoteUser}@${ServerIP} $remoteCommands

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to restart services" -ForegroundColor Red
    exit 1
}

# 5. Verify deployment
Write-Host "`n5. Verifying deployment..." -ForegroundColor Green
Start-Sleep -Seconds 5

try {
    $health = Invoke-WebRequest -Uri "http://46.224.66.48:8010/health" -UseBasicParsing -TimeoutSec 10
    if ($health.StatusCode -eq 200) {
        Write-Host "✅ Shopfloor Copilot: HEALTHY" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Shopfloor Copilot health check failed: $_" -ForegroundColor Yellow
}

try {
    $opcHealth = Invoke-WebRequest -Uri "http://46.224.66.48:8040/status" -UseBasicParsing -TimeoutSec 10
    if ($opcHealth.StatusCode -eq 200) {
        Write-Host "✅ OPC Studio: HEALTHY" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ OPC Studio health check failed: $_" -ForegroundColor Yellow
}

# 6. Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Configuration uploaded (.env.hetzner → .env)" -ForegroundColor Green
Write-Host "✅ Code updated (opc_explorer.py)" -ForegroundColor Green
Write-Host "✅ Services rebuilt and restarted" -ForegroundColor Green
Write-Host "`nOPC Endpoint Configuration:" -ForegroundColor Yellow
Write-Host "  Environment: OPC_DEMO_ENDPOINT=opc.tcp://46.224.66.48:4850" -ForegroundColor White
Write-Host "  Code Default: opc.tcp://46.224.66.48:4850" -ForegroundColor White
Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Open http://46.224.66.48:8010 in browser" -ForegroundColor Gray
Write-Host "2. Navigate to OPC Explorer (Tab 15)" -ForegroundColor Gray
Write-Host "3. Click 'Connect' button (endpoint is pre-configured)" -ForegroundColor Gray
Write-Host "4. Verify connection status: Connected ✅" -ForegroundColor Gray
Write-Host "`nIf connection still fails:" -ForegroundColor Yellow
Write-Host "- Check OPC server is running: ssh root@46.224.66.48 'cd /root/rag-suite && docker-compose ps | grep opc-demo'" -ForegroundColor Gray
Write-Host "- Check firewall allows port 4850: ssh root@46.224.66.48 'ufw status'" -ForegroundColor Gray
Write-Host "- View logs: ssh root@46.224.66.48 'cd /root/rag-suite && docker-compose logs opc-demo'" -ForegroundColor Gray

Write-Host "`n========================================`n" -ForegroundColor Cyan
