# Deploy fix scripts to Hetzner and run diagnostics
# Usage: .\deploy-hetzner-fix.ps1

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "46.224.66.48",
    
    [Parameter(Mandatory=$false)]
    [string]$User = "root",
    
    [Parameter(Mandatory=$false)]
    [switch]$RunFix
)

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  Hetzner Fix Deployment" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Target: $User@$ServerIP" -ForegroundColor Yellow
Write-Host ""

# Check if ssh is available
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ SSH not found. Please install OpenSSH client." -ForegroundColor Red
    exit 1
}

# Check if scp is available
if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "❌ SCP not found. Please install OpenSSH client." -ForegroundColor Red
    exit 1
}

# Test SSH connection
Write-Host "Testing SSH connection..." -ForegroundColor Cyan
try {
    $result = ssh -o ConnectTimeout=10 "$User@$ServerIP" "echo 'Connected'"
    if ($result -eq "Connected") {
        Write-Host "✅ SSH connection successful" -ForegroundColor Green
    } else {
        Write-Host "❌ SSH connection failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Cannot connect to $ServerIP" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""

# Check if app directory exists
Write-Host "Checking deployment directory..." -ForegroundColor Cyan
$appDir = "/opt/shopfloor/rag-suite"
Write-Host "  App directory: $appDir" -ForegroundColor Gray

# Upload diagnostic script
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Uploading diagnostic script..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

scp -o ConnectTimeout=10 "hetzner-diagnose.sh" "$User@${ServerIP}:~/hetzner-diagnose.sh"
ssh "$User@$ServerIP" "chmod +x ~/hetzner-diagnose.sh"
Write-Host "✅ Diagnostic script uploaded" -ForegroundColor Green

# Upload fix script
Write-Host ""
Write-Host "Uploading fix script..." -ForegroundColor Cyan
scp -o ConnectTimeout=10 "hetzner-fix.sh" "$User@${ServerIP}:~/hetzner-fix.sh"
ssh "$User@$ServerIP" "chmod +x ~/hetzner-fix.sh"
Write-Host "✅ Fix script uploaded" -ForegroundColor Green

# Upload database backup
Write-Host ""
Write-Host "Checking database backup..." -ForegroundColor Cyan
if (Test-Path "ragdb_backup_utf8.sql") {
    Write-Host "  Found: ragdb_backup_utf8.sql" -ForegroundColor Gray
    $fileSize = (Get-Item "ragdb_backup_utf8.sql").Length / 1MB
    Write-Host "  Size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Gray
    
    Write-Host "  Uploading (this may take a moment)..." -ForegroundColor Yellow
    scp -o ConnectTimeout=10 "ragdb_backup_utf8.sql" "$User@${ServerIP}:~/ragdb_backup_utf8.sql"
    Write-Host "✅ Database backup uploaded" -ForegroundColor Green
} else {
    Write-Host "⚠️  ragdb_backup_utf8.sql not found - skipping" -ForegroundColor Yellow
    Write-Host "   The fix script will need this file to restore data" -ForegroundColor Yellow
}

# Run diagnostics
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Running diagnostics on Hetzner..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

ssh "$User@$ServerIP" "cd /opt/shopfloor/rag-suite && bash ~/hetzner-diagnose.sh"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  Diagnostics Complete" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

# Ask if user wants to run the fix
if ($RunFix) {
    $runFix = "y"
} else {
    $runFix = Read-Host "Do you want to run the fix now? (y/n)"
}

if ($runFix -eq "y" -or $runFix -eq "Y") {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host "Running fix script..." -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host ""
    
    ssh "$User@$ServerIP" "cd /opt/shopfloor/rag-suite && bash ~/hetzner-fix.sh"
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  ✅ Fix Applied!" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your Hetzner deployment should now be working with data visible." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "To run the fix manually, SSH into your server and run:" -ForegroundColor Yellow
    Write-Host "  ssh $User@$ServerIP" -ForegroundColor Cyan
    Write-Host "  cd /opt/shopfloor/rag-suite" -ForegroundColor Cyan
    Write-Host "  bash ~/hetzner-fix.sh" -ForegroundColor Cyan
}

Write-Host ""
