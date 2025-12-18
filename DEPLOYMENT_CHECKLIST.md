# 🚀 Hetzner Deployment Checklist
**Server:** 46.224.66.48  
**Primary Domain:** shopfloor-copilot.com  
**Secondary Domain:** opc-studio.com  
**Date:** December 18, 2025

---

## ✅ Pre-Deployment (Do This First)

### DNS Configuration
- [ ] Point `shopfloor-copilot.com` A record to `46.224.66.48`
- [ ] Point `www.shopfloor-copilot.com` A record to `46.224.66.48`
- [ ] Point `opc-studio.com` A record to `46.224.66.48`
- [ ] Point `www.opc-studio.com` A record to `46.224.66.48`
- [ ] Wait 5-10 minutes for DNS propagation
- [ ] Test: `nslookup shopfloor-copilot.com`

---

## 📦 Deployment Steps

### Step 1: Connect to Server
```bash
ssh root@46.224.66.48
# Password: jvN9RqLbnqah3tta3KXv
```

### Step 2: Update System
```bash
apt-get update
apt-get upgrade -y
apt-get install -y curl wget git htop
```

### Step 3: Install Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
docker --version
```

### Step 4: Install Dependencies
```bash
apt-get install -y nginx certbot python3-certbot-nginx ufw fail2ban
```

### Step 5: Configure Firewall
```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable
ufw status
```

### Step 6: Create Deployment Directory
```bash
mkdir -p /opt/shopfloor
cd /opt/shopfloor
```

### Step 7: Transfer Files from Windows

**Option A: Using WinSCP**
1. Download WinSCP: https://winscp.net/
2. Connect to: `46.224.66.48` (root / jvN9RqLbnqah3tta3KXv)
3. Upload entire `rag-suite` folder to `/opt/shopfloor/`

**Option B: Using PowerShell SCP**
```powershell
# Run from: C:\Users\Davide\VS-Code Solutions\rag-suite
scp -r * root@46.224.66.48:/opt/shopfloor/
```

**Option C: Using Git**
```bash
# On server
cd /opt/shopfloor
git clone YOUR_REPO_URL .
```

### Step 8: Configure Production Environment
```bash
cd /opt/shopfloor
cp docker-compose.prod.yml docker-compose.yml
cp .env.prod .env

# Verify files
ls -la
cat .env
```

### Step 9: Build Docker Images
```bash
cd /opt/shopfloor
docker compose build

# This will take 5-10 minutes
# Expected output: Successfully built images
```

### Step 10: Start Services
```bash
docker compose up -d

# Check status
docker compose ps

# Check logs
docker compose logs -f shopfloor
docker compose logs -f opc-studio
```

### Step 11: Configure Nginx
```bash
# Copy nginx config
cp /opt/shopfloor/nginx-config.conf /etc/nginx/sites-available/shopfloor

# Enable site
ln -s /etc/nginx/sites-available/shopfloor /etc/nginx/sites-enabled/

# Remove default site
rm /etc/nginx/sites-enabled/default

# Test configuration
nginx -t

# Reload Nginx
systemctl reload nginx
```

### Step 12: Obtain SSL Certificates
```bash
# Primary domain
certbot --nginx -d shopfloor-copilot.com -d www.shopfloor-copilot.com --non-interactive --agree-tos --email admin@shopfloor-copilot.com

# Secondary domain
certbot --nginx -d opc-studio.com -d www.opc-studio.com --non-interactive --agree-tos --email admin@opc-studio.com

# Verify SSL
certbot certificates
```

### Step 13: Test Services
```bash
# Test locally on server
curl http://localhost:8010/health
curl http://localhost:8040/health

# Test via domain (from your Windows machine)
curl https://shopfloor-copilot.com/health
curl https://opc-studio.com/health
```

### Step 14: Setup Monitoring
```bash
cd /opt/shopfloor/scripts
chmod +x *.sh
./setup-cron.sh

# Verify cron jobs
crontab -l
```

### Step 15: Download Ollama Model
```bash
# Download AI model (required for diagnostics)
docker exec -it shopfloor-ollama ollama pull llama3.1:8b

# Verify
docker exec -it shopfloor-ollama ollama list
```

---

## 🔍 Verification Tests

### Test 1: Service Health
```bash
docker compose ps
# All services should show "Up"
```

### Test 2: Database Connection
```bash
docker exec -it shopfloor-postgres psql -U postgres -d ragdb -c "\dt"
# Should show database tables
```

### Test 3: Web Interface
- Open browser: https://shopfloor-copilot.com
- Should see Shopfloor Copilot dashboard
- Open browser: https://opc-studio.com
- Should see OPC Studio interface

### Test 4: API Endpoints
```bash
curl https://shopfloor-copilot.com/health
# Should return: {"status": "healthy"}

curl https://opc-studio.com/health
# Should return: {"status": "ok"}
```

### Test 5: SSL Configuration
```bash
curl -I https://shopfloor-copilot.com
# Should return 200 OK with SSL headers
```

---

## 🛡️ Security Hardening

### Create Non-Root User
```bash
adduser deploy
usermod -aG docker deploy
usermod -aG sudo deploy

# Test
su - deploy
docker ps
```

### Disable Root SSH Login
```bash
nano /etc/ssh/sshd_config
# Change: PermitRootLogin no
# Change: PasswordAuthentication no (after setting up SSH keys)

systemctl restart sshd
```

### Configure Fail2ban
```bash
systemctl enable fail2ban
systemctl start fail2ban
fail2ban-client status
```

---

## 📊 Post-Deployment

### Monitor Services
```bash
# View logs
docker compose logs -f

# Resource usage
docker stats

# Health check
/opt/shopfloor/scripts/health-check.sh
```

### First Backup
```bash
/opt/shopfloor/scripts/backup.sh
ls -lh /opt/shopfloor/backups/
```

### Grafana Setup (Optional)
- URL: https://shopfloor-copilot.com:3000
- Default: admin / admin
- Configure dashboards for monitoring

---

## 🆘 Troubleshooting

### Services Not Starting
```bash
docker compose down
docker compose up -d
docker compose logs
```

### SSL Certificate Issues
```bash
certbot renew --dry-run
systemctl restart nginx
```

### Database Connection Issues
```bash
docker compose restart postgres
docker compose logs postgres
```

### Out of Disk Space
```bash
df -h
docker system prune -a --volumes
```

### High Memory Usage
```bash
free -h
docker stats
# Restart services if needed
docker compose restart
```

---

## 📝 Important Credentials

**Server Access:**
- IP: 46.224.66.48
- User: root
- Password: jvN9RqLbnqah3tta3KXv

**Database:**
- User: postgres
- Password: (in .env.prod file)
- Database: ragdb

**Application:**
- Secret Key: (in .env.prod file)
- Admin Email: admin@shopfloor-copilot.com

**Domains:**
- Primary: https://shopfloor-copilot.com
- Secondary: https://opc-studio.com

---

## 🔗 Next Steps

1. **Configure OPC Connection**
   - Point OPC UA client to: opc.tcp://46.224.66.48:4840
   - Or use domain: opc.tcp://opc-studio.com:4840

2. **Ingest Documents**
   ```bash
   # From Windows machine
   curl -X POST https://shopfloor-copilot.com/api/ingest \
     -F "file=@your-manual.pdf"
   ```

3. **Create First User**
   - Visit: https://shopfloor-copilot.com
   - Register operator account

4. **Test AI Diagnostics**
   - Ask: "What's wrong with Station A1?"
   - Should return analysis with citations

---

## ✅ Deployment Complete!

Your Shopfloor Copilot is now running in production on Hetzner Cloud.

**Access URLs:**
- 🏭 Shopfloor Copilot: https://shopfloor-copilot.com
- 🔧 OPC Studio: https://opc-studio.com
- 📊 Grafana (optional): https://shopfloor-copilot.com:3000

**Estimated Monthly Cost:** €15-20/month

**Support:** Contact your DevOps team for issues
