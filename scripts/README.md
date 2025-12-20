# Deployment Scripts

This directory contains production-ready automation scripts for deploying and maintaining Shopfloor Copilot on Hetzner Cloud.

## 📁 Scripts Overview

### 1. generate_live_data.py
**Automated live OEE data generation**

**Usage:**
```bash
cd scripts
POSTGRES_HOST=localhost POSTGRES_PASSWORD=your_password python3 generate_live_data.py
```

**What it does:**
- Generates realistic OEE data for current shift (M/A/N)
- Updates all 11 production lines
- Creates station-level performance data (3 stations per line)
- Uses ON CONFLICT to update existing records (no duplicates)
- Automatically cleans up data older than 45 days

**Shifts:**
- Morning (M): 6:00-14:00
- Afternoon (A): 14:00-22:00
- Night (N): 22:00-6:00

**Schedule:** Run hourly (top of every hour) via cron  
**Output:** All dashboards show fresh, current data  
**Log:** `/var/log/shopfloor-datagen.log`

**Dependencies:** `python3-psycopg` (install with `apt-get install python3-psycopg`)

---

### 2. hetzner-deploy.sh
**Automated deployment to Hetzner Cloud**

**Usage:**
```bash
./scripts/hetzner-deploy.sh SERVER_IP DOMAIN [EMAIL]
```

**Example:**
```bash
./scripts/hetzner-deploy.sh 123.45.67.89 shopfloor.example.com admin@example.com
```

**What it does:**
- Connects to Hetzner server via SSH
- Installs Docker, Nginx, Certbot, UFW, Fail2ban
- Configures firewall rules
- Copies project files
- Generates secure passwords
- Builds Docker images
- Starts all services
- Obtains SSL certificate from Let's Encrypt

**Time:** ~10-15 minutes  
**Prerequisites:** SSH access to server, domain DNS configured

---

### 3. backup.sh
**Automated backup of all data**

**Usage:**
```bash
./scripts/backup.sh
```

**What it backs up:**
- PostgreSQL database (compressed SQL dump)
- ChromaDB vector store
- Configuration files
- OPC Studio semantic mappings

**Schedule:** Run daily at 2 AM via cron  
**Retention:** 7 days (configurable)  
**Location:** `~/shopfloor-deploy/backups/`

---

### 4. restore.sh
**Restore from backup**

**Usage:**
```bash
./scripts/restore.sh BACKUP_DATE
```

**Example:**
```bash
# List available backups
./scripts/restore.sh

# Restore specific backup
./scripts/restore.sh 20251218_020000
```

**What it does:**
- Stops all services
- Restores PostgreSQL database
- Restores ChromaDB
- Restores configuration files
- Restarts services
- Verifies health

**Use case:** Disaster recovery, rollback after failed update

---

### 5. health-check.sh
**Monitor service health**

**Usage:**
```bash
./scripts/health-check.sh
```

**What it checks:**
- Docker daemon status
- All container health
- HTTP endpoint availability
- Disk space usage
- Memory usage

**Schedule:** Run every 5 minutes via cron  
**Alerts:** Email + Slack (optional)  
**Exit code:** 0 = healthy, 1 = failure

---

### 6. setup-cron.sh
**Install cron jobs**

**Usage:**
```bash
./scripts/setup-cron.sh
```

**What it installs:**
- Hourly live data generation (top of every hour)
- Daily backups (2 AM)
- Health checks (every 5 minutes)
- Weekly Docker cleanup (Sunday 3 AM)
- Daily log rotation (4 AM)
- Monthly SSL renewal check (1st of month)

**Run once:** After initial deployment

**Cron Jobs Installed:**
```cron
# Generate live OEE data every hour
0 * * * * cd /opt/shopfloor/rag-suite/scripts && POSTGRES_HOST=localhost POSTGRES_PASSWORD=xxx python3 generate_live_data.py >> /var/log/shopfloor-datagen.log 2>&1

# Daily backup at 2 AM
0 2 * * * /opt/shopfloor/rag-suite/scripts/backup.sh >> /var/log/shopfloor-backup.log 2>&1

# Health check every 5 minutes
*/5 * * * * /opt/shopfloor/rag-suite/scripts/health-check.sh >> /var/log/shopfloor-health.log 2>&1

# Weekly Docker cleanup on Sunday at 3 AM
0 3 * * 0 docker system prune -af --volumes >> /var/log/shopfloor-cleanup.log 2>&1

# Rotate logs daily at 4 AM
0 4 * * * find /var/log -name "shopfloor-*.log" -type f -mtime +7 -delete

# SSL certificate renewal check (Let's Encrypt auto-renews, but check monthly)
0 5 1 * * sudo certbot renew --quiet
```

---

## 🚀 Quick Start

### First-Time Deployment

```bash
# 1. Make scripts executable
chmod +x scripts/*.sh

# 2. Deploy to Hetzner
./scripts/hetzner-deploy.sh YOUR_SERVER_IP shopfloor.yourcompany.com

# 3. SSH to server and setup cron
ssh deploy@YOUR_SERVER_IP
cd shopfloor-deploy
./scripts/setup-cron.sh
```

### Daily Operations

```bash
# Manual backup
./scripts/backup.sh

# Check health
./scripts/health-check.sh

# View logs
docker compose logs -f shopfloor
```

---

## 🔧 Configuration

### Environment Variables

Edit these before deployment:

**In hetzner-deploy.sh:**
- `DEPLOY_USER` - Default: "deploy"
- `ALERT_EMAIL` - For health check alerts

**In backup.sh:**
- `RETENTION_DAYS` - Default: 7
- `BACKUP_DIR` - Default: ~/shopfloor-deploy/backups

**In health-check.sh:**
- `ALERT_EMAIL` - Email for alerts
- `SLACK_WEBHOOK` - Slack webhook URL (optional)

---

## 📊 Monitoring

### Check Cron Jobs
```bash
# View installed cron jobs
crontab -l

# View cron logs
tail -f /var/log/shopfloor-backup.log
tail -f /var/log/shopfloor-health.log
```

### Check Backups
```bash
# List backups
ls -lh ~/shopfloor-deploy/backups/

# Check backup sizes
du -sh ~/shopfloor-deploy/backups/*
```

### Check Service Status
```bash
# All services
docker compose ps

# Specific service logs
docker compose logs -f shopfloor

# Resource usage
docker stats
```

---

## 🆘 Troubleshooting

### Script Fails with "Permission Denied"
```bash
chmod +x scripts/*.sh
```

### SSH Connection Fails
```bash
# Check SSH key
ssh-add -l

# Test connection
ssh -v deploy@SERVER_IP
```

### Backup Fails
```bash
# Check disk space
df -h

# Check container status
docker ps | grep postgres

# Run manually to see errors
./scripts/backup.sh
```

### Health Check False Alarms
```bash
# Adjust thresholds in health-check.sh
# Default: Disk > 85%, Memory > 90%

# Disable alerts temporarily
crontab -e
# Comment out health-check line
```

---

## 🔒 Security Notes

### Secrets Management
- Never commit `.env` files with real passwords
- Use `openssl rand -base64 32` to generate secure passwords
- Store backup credentials separately

### SSH Keys
- Use separate keys for deployment vs. personal access
- Rotate keys annually
- Use passphrase-protected keys

### Backup Security
- Backups contain sensitive data
- Encrypt backups if storing off-site
- Use `rclone` with encryption for cloud backups

---

## 🎯 Best Practices

### Before Running Scripts
1. Read the script to understand what it does
2. Test on dev/staging environment first
3. Have a backup before major changes
4. Document any customizations

### Backup Strategy
- Keep 7 days of daily backups
- Keep 4 weekly backups
- Keep 12 monthly backups
- Test restore procedure quarterly

### Monitoring
- Review health check logs weekly
- Set up Grafana dashboards
- Configure alerting for critical services
- Monitor costs monthly

---

## 📝 Maintenance Schedule

### Daily (Automated)
- ✅ Backup at 2 AM
- ✅ Health checks every 5 minutes
- ✅ Log rotation at 4 AM

### Weekly
- Review monitoring dashboards
- Check backup integrity
- Review security logs
- Update Docker images

### Monthly
- Security updates (`apt upgrade`)
- Review and optimize costs
- Test backup restore
- Review cron job logs

---

## 🔗 Related Documentation

- [Complete Hetzner Deployment Guide](../docs/HETZNER_DEPLOYMENT.md)
- [Quick Start Guide](../docs/HETZNER_QUICKSTART.md)
- [Deployment Summary](../docs/HETZNER_SUMMARY.md)
- [System Documentation](../docs/shopfloor-copilot/README.md)

---

## 📞 Support

For issues with scripts:
1. Check script logs: `/var/log/shopfloor-*.log`
2. Run manually to see errors
3. Review documentation above
4. Contact devops@yourcompany.com

---

**Last Updated:** December 18, 2025  
**Scripts Version:** 1.0  
**Tested On:** Ubuntu 22.04 LTS
