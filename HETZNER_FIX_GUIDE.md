# Hetzner Data Fix - Quick Guide

## Problem
Data is not visible in the Hetzner deployment (same issue as local).

## Root Cause
Most likely the PostgreSQL database is empty or not properly initialized with OEE data.

## Solution - 3 Easy Steps

### Option A: Automated Fix (Recommended)

**From your Windows machine:**

```powershell
# Run this from the rag-suite directory (IP and user pre-configured)
.\deploy-hetzner-fix.ps1 -RunFix
```

This will:
1. Upload diagnostic and fix scripts to your server
2. Upload the database backup
3. Run diagnostics
4. Restore the database
5. Restart all services

### Option B: Manual Fix

**1. SSH into your Hetzner server:**
```bash
ssh root@46.224.66.48
cd /opt/shopfloor/rag-suite
```

**2. Upload the database backup:**
From your local machine:
```powershell
scp ragdb_backup_utf8.sql root@46.224.66.48:/opt/shopfloor/rag-suite/
```

**3. Run diagnostics:**
```bash
# Check what's wrong
docker compose ps
docker compose logs postgres --tail=50
docker compose logs shopfloor --tail=50
```

**4. Restore the database:**
```bash
# Stop services
docker compose down

# Start only PostgreSQL
docker compose up -d postgres

# Wait for it to be ready (10-15 seconds)
sleep 15

# Restore data
cat ragdb_backup_utf8.sql | docker compose exec -T postgres psql -U postgres -d ragdb

# Verify
docker compose exec postgres psql -U postgres -d ragdb -c "SELECT COUNT(*) FROM oee_line_shift;"

# Start all services
docker compose --profile hetzner up -d

# Check status
docker compose ps
```

**5. Verify the fix:**
```bash
# Check health endpoints
curl http://localhost:8010/health
curl http://localhost:8040/health

# Check logs
docker compose logs -f
```

## Common Issues & Fixes

### Issue 1: PostgreSQL container not running
```bash
# Check why
docker compose logs postgres

# Restart
docker compose restart postgres
```

### Issue 2: Port conflicts (if using local postgres)
Same fix as local - use alternate port or disable local PostgreSQL service

### Issue 3: Database exists but is empty
```bash
# Check row count
docker compose exec postgres psql -U postgres -d ragdb -c "SELECT COUNT(*) FROM oee_line_shift;"

# If 0, restore backup
cat ragdb_backup_utf8.sql | docker compose exec -T postgres psql -U postgres -d ragdb
```

### Issue 4: Services unhealthy after startup
```bash
# Give them more time
sleep 30
docker compose ps

# If still unhealthy, check logs
docker compose logs shopfloor --tail=100
docker compose logs opc-studio --tail=100
```

### Issue 5: Ollama not starting (if using --profile hetzner)
```bash
# Check if Ollama is needed
docker compose --profile hetzner ps

# If Ollama container is missing or failing
docker compose logs ollama

# May need to pull model
docker compose exec ollama ollama pull llama3.2:3b
```

## Files Created

1. **`hetzner-diagnose.sh`** - Diagnostic script (runs on Hetzner)
2. **`hetzner-fix.sh`** - Automated fix script (runs on Hetzner)
3. **`deploy-hetzner-fix.ps1`** - Deploy and run from Windows
4. **`docker-compose.local.yml`** - Local development config (already created)

## Quick Commands Reference

### From your Windows machine:
```powershell
# Deploy and run full fix
.\deploy-hetzner-fix.ps1 -ServerIP "YOUR_IP" -User "deploy" -RunFix

# Just run diagnostics
.\deploy-hetzner-fix.ps1 -ServerIP "YOUR_IP" -User "deploy"
```

### On Hetzner server:
```bash
# Quick status check
docker compose ps

# View all logs
docker compose logs -f

# Restart everything
docker compose restart

# Full rebuild
docker compose down
docker compose up -d --build

# Check database
docker compose exec postgres psql -U postgres -d ragdb -c "SELECT COUNT(*) FROM oee_line_shift;"
```

## Expected Results

After the fix:
- ✅ PostgreSQL: healthy, with 3000+ rows
- ✅ Shopfloor Copilot: http://YOUR_DOMAIN:8010 (or via nginx)
- ✅ OPC Studio: http://YOUR_DOMAIN:8040
- ✅ All dashboards showing data
- ✅ 11 production lines visible
- ✅ Real-time updates working

## Support

If issues persist:
1. Run diagnostics: `bash ~/hetzner-diagnose.sh`
2. Check logs: `docker compose logs -f`
3. Verify .env file has correct DATABASE_URL
4. Check disk space: `df -h`
5. Check memory: `free -h`

## Next Steps

After data is visible:
1. Set up automated backups (cron job)
2. Configure monitoring (Prometheus/Grafana)
3. Set up SSL/TLS with Let's Encrypt
4. Configure Nginx reverse proxy
5. Set up log rotation

---

**Need Help?**
Run the automated diagnostic: `bash ~/hetzner-diagnose.sh`
