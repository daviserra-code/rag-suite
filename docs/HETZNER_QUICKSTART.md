# Hetzner Deployment - Quick Reference

## 🚀 5-Minute Production Deployment

### Prerequisites
- Hetzner Cloud account
- Domain name
- SSH key pair
- Git repository access

### Deploy Commands

```bash
# 1. Create server (via CLI)
hcloud server create --name shopfloor-prod --type cx41 --image ubuntu-22.04 --location nbg1 --ssh-key your-key

# 2. Get server IP
export SERVER_IP=$(hcloud server ip shopfloor-prod)

# 3. Clone and setup
git clone https://github.com/yourorg/rag-suite.git
cd rag-suite

# 4. Run automated deployment
./scripts/hetzner-deploy.sh $SERVER_IP shopfloor.yourcompany.com

# 5. Access application
open https://shopfloor.yourcompany.com
```

---

## 📊 Server Sizing Guide

### Small Plant (< 100 stations)
```
Type: CX41
- 4 vCPU
- 16 GB RAM
- €15/month
- Capacity: 200 stations, 20 users
```

### Medium Plant (100-300 stations)
```
Type: CX51
- 8 vCPU
- 32 GB RAM
- €30/month
- Capacity: 500 stations, 50 users
```

### Large Plant (> 300 stations)
```
Multi-server setup
- App: CX51 (€30)
- DB: CPX41 (€22)
- Storage: CX21 (€5)
- Total: ~€80/month
```

---

## 🔒 Security Checklist

- [ ] SSH key-based auth only (no passwords)
- [ ] Firewall rules configured (Hetzner + UFW)
- [ ] Fail2ban installed
- [ ] SSL certificate installed (Let's Encrypt)
- [ ] Non-root user created
- [ ] Automatic security updates enabled
- [ ] Docker socket protected
- [ ] Environment secrets secured
- [ ] VPN configured for factory access

---

## 📦 Deployment Options

### Option 1: Single Server (Recommended for Start)
**Time:** 30 minutes  
**Cost:** €15-30/month  
**Capacity:** Up to 200 stations

### Option 2: Multi-Server
**Time:** 2 hours  
**Cost:** €60-80/month  
**Capacity:** 500+ stations  
**Features:** Load balancing, HA

### Option 3: Hybrid (Cloud + On-Premise)
**Time:** 4 hours  
**Cost:** €30/month + on-prem hardware  
**Use case:** Data sovereignty, regulatory compliance

---

## 🔧 Common Commands

### Server Management
```bash
# SSH into server
ssh deploy@SERVER_IP

# Check service status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f shopfloor

# Restart service
docker compose -f docker-compose.prod.yml restart shopfloor
```

### Monitoring
```bash
# Check resources
htop
df -h
docker stats

# View Prometheus
open http://SERVER_IP:9090

# View Grafana
open http://SERVER_IP:3000
```

### Backups
```bash
# Manual backup
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh backups/postgres_20251218_020000.sql.gz

# List backups
ls -lh backups/
```

---

## 🆘 Emergency Procedures

### Service Down
```bash
# 1. Check status
docker compose -f docker-compose.prod.yml ps

# 2. Check logs
docker compose -f docker-compose.prod.yml logs --tail=100 shopfloor

# 3. Restart service
docker compose -f docker-compose.prod.yml restart shopfloor
```

### Database Issues
```bash
# Check PostgreSQL
docker exec shopfloor-postgres psql -U shopfloor -c "SELECT 1;"

# Restore from backup
docker exec -i shopfloor-postgres psql -U shopfloor shopfloor_mes < backups/latest.sql
```

### Out of Disk Space
```bash
# Clean Docker
docker system prune -af --volumes

# Check large directories
du -sh /* | sort -h

# Rotate logs
truncate -s 0 /var/log/nginx/access.log
```

### High CPU/Memory
```bash
# Check resource usage
docker stats

# Restart heavy service
docker compose -f docker-compose.prod.yml restart ollama

# Scale down temporarily
docker compose -f docker-compose.prod.yml scale shopfloor=1
```

---

## 📝 Configuration Files

### Quick Edit Locations

**Environment Variables:**
```
config/env/production.env
```

**Nginx Config:**
```
config/nginx/conf.d/shopfloor.conf
```

**Semantic Mappings:**
```
opc-studio/config/semantic_mappings.yaml
```

**Docker Compose:**
```
docker-compose.prod.yml
```

---

## 💰 Cost Breakdown

| Component | Monthly Cost |
|-----------|--------------|
| CX41 Server | €15.30 |
| Automated Backups | €3.06 |
| Domain (Namecheap) | €1.00 |
| **Total** | **€19.36** |

### Cost Optimization Tips
- Use Hetzner Storage Box for backups (€3.81/100GB)
- Enable auto-shutdown during non-production hours
- Use spot instances for dev/test (when available)
- Compress Docker images
- Use CDN (Cloudflare free tier) for static assets

---

## 🎯 Performance Targets

| Metric | Target | Command to Check |
|--------|--------|------------------|
| API Response | < 200ms | `curl -w "%{time_total}" https://domain/health` |
| Diagnostic Time | < 20s | Check UI timer |
| OPC Read Latency | < 100ms | Check OPC Studio logs |
| Database Query | < 50ms | Check Grafana dashboard |
| CPU Usage | < 70% | `htop` |
| Memory Usage | < 80% | `free -h` |
| Disk Usage | < 85% | `df -h` |

---

## 📱 Monitoring & Alerts

### Grafana Dashboards
1. **System Overview** - CPU, RAM, Disk, Network
2. **Application Metrics** - Request rate, latency, errors
3. **Docker Metrics** - Container stats, image sizes
4. **OPC Studio** - Connection status, read/write rates
5. **AI Diagnostics** - LLM response times, RAG queries

### Alert Channels
- Email: admin@yourcompany.com
- Slack: #shopfloor-alerts
- SMS: Via Twilio (optional)

---

## 🔄 Update Procedure

### Rolling Update (Zero Downtime)
```bash
# 1. Pull new images
docker compose -f docker-compose.prod.yml pull

# 2. Backup database
./scripts/backup.sh

# 3. Update services one by one
docker compose -f docker-compose.prod.yml up -d --no-deps shopfloor

# 4. Verify health
curl -f https://domain/health

# 5. Repeat for other services
```

### Emergency Rollback
```bash
# Restore previous version
docker compose -f docker-compose.prod.yml down
docker tag shopfloor-copilot:previous shopfloor-copilot:latest
docker compose -f docker-compose.prod.yml up -d
```

---

## 📞 Support Contacts

| Issue | Contact | Response Time |
|-------|---------|---------------|
| Hetzner Infrastructure | support@hetzner.com | < 24h |
| Application Issues | devops@yourcompany.com | < 4h |
| Emergency | +49-XXX-XXXXXXX | Immediate |

---

## ✅ Post-Deployment Checklist

**Week 1:**
- [ ] Monitor resource usage daily
- [ ] Verify backups are running
- [ ] Test restore procedure
- [ ] Configure alerts
- [ ] Train operators

**Week 2:**
- [ ] Review logs for errors
- [ ] Optimize slow queries
- [ ] Set up monitoring dashboards
- [ ] Document runbook

**Month 1:**
- [ ] Security audit
- [ ] Cost analysis
- [ ] Performance review
- [ ] Backup integrity test

---

## 🔗 Useful Links

- **Hetzner Console:** https://console.hetzner.cloud/
- **Documentation:** https://docs.hetzner.com/
- **Status Page:** https://status.hetzner.com/
- **Pricing:** https://www.hetzner.com/cloud#pricing
- **Community:** https://community.hetzner.com/

---

**Quick Deploy Command:**
```bash
curl -sSL https://raw.githubusercontent.com/yourorg/rag-suite/main/scripts/hetzner-install.sh | bash
```

**Estimated Total Setup Time:** 30-60 minutes (first deployment)

**Production-Ready:** Yes ✅
