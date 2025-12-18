# Git commit script for deployment infrastructure
Set-Location "c:\Users\Davide\VS-Code Solutions\rag-suite"

Write-Host "Staging all files..." -ForegroundColor Cyan
git add .

Write-Host "Committing..." -ForegroundColor Cyan
git commit -m "Add Hetzner deployment infrastructure

- Complete deployment documentation (24,000+ words)
- Production docker-compose configuration  
- Nginx reverse proxy setup
- Automated deployment scripts (hetzner-deploy.sh)
- Backup/restore automation scripts
- Health monitoring script
- Cron job setup script
- Deployment checklist
- Cost optimization (75% cheaper than AWS/Azure)
- SSL/TLS configuration
- Security hardening procedures"

Write-Host "Pushing to remote..." -ForegroundColor Cyan
git push

Write-Host "Done!" -ForegroundColor Green
