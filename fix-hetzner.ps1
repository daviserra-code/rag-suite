# Quick Fix for Hetzner - One Command
# This connects to your server and fixes everything

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  Hetzner Quick Fix - Connecting..." -ForegroundColor Green
Write-Host "  Server: 46.224.66.48" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

# Run the full automated fix
.\deploy-hetzner-fix.ps1 -RunFix

Write-Host ""
Write-Host "Done! Check your application at:" -ForegroundColor Green
Write-Host "  https://shopfloor-copilot.com" -ForegroundColor Cyan
Write-Host "  https://opc-studio.com:8040" -ForegroundColor Cyan
