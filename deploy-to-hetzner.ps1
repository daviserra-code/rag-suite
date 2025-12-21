#!/usr/bin/env pwsh
# Hetzner Quick Deployment Script
# Deploys latest code to Hetzner server

param(
    [string]$Server = "167.235.73.34",
    [string]$User = "root",
    [string]$ComposeFile = "docker-compose.prod.yml"
)

Write-Host "🚀 Deploying Shopfloor Copilot to Hetzner..." -ForegroundColor Cyan
Write-Host "   Server: $Server" -ForegroundColor Gray
Write-Host "   User: $User" -ForegroundColor Gray
Write-Host ""

$commands = @(
    "cd /root/rag-suite",
    "echo '📥 Pulling latest code...'",
    "git pull origin main",
    "echo '🐳 Building and starting services...'",
    "docker-compose -f $ComposeFile pull",
    "docker-compose -f $ComposeFile up -d --build data-simulator",
    "docker-compose -f $ComposeFile restart shopfloor",
    "echo '⏳ Waiting for services to stabilize...'",
    "sleep 10",
    "echo '📊 Container status:'",
    "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'shopfloor|opc-studio'",
    "echo ''",
    "echo '📝 Recent data-simulator logs:'",
    "docker logs --tail 20 shopfloor-data-sim 2>&1 | tail -10",
    "echo ''",
    "echo '✅ Deployment complete!'"
)

$sshCommand = $commands -join ' && '

Write-Host "Connecting to $Server..." -ForegroundColor Yellow

try {
    ssh "${User}@${Server}" $sshCommand
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Deployment successful!" -ForegroundColor Green
        Write-Host "🌐 Application: http://$Server:8010" -ForegroundColor Cyan
        Write-Host "🔧 OPC Studio: http://$Server:8040" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Deployment failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "❌ SSH connection failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check SSH key: ssh-add -l" -ForegroundColor Gray
    Write-Host "  2. Test connection: ssh ${User}@${Server} 'echo OK'" -ForegroundColor Gray
    Write-Host "  3. Manual deploy: ssh ${User}@${Server}" -ForegroundColor Gray
    exit 1
}
