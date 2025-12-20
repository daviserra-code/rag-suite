# ChatGPT Alignment - Shopfloor Copilot & OPC-Studio

**Last Updated:** December 20, 2025  
**Project Status:** Production Deployment - Phase 4 Complete  
**Production URL:** https://shopfloor-copilot.com

---

## 1. Project Overview

**Shopfloor Copilot** is a multi-tenant RAG-based AI platform deployed on Hetzner Cloud, featuring:
- Real-time OEE (Overall Equipment Effectiveness) monitoring
- Production line analytics with live dashboards
- PDF/CSV export capabilities
- Automated data generation and reporting
- NiceGUI-based interactive interface

**Architecture:**
- FastAPI 0.115.2 + NiceGUI 2.5.0
- PostgreSQL 16 (production database)
- ChromaDB 0.5.20 (vector database)
- Ollama llama3.1:8b (LLM)
- Nginx reverse proxy with SSL
- Docker Compose (6 containers)

---

## 2. Production Environment

### Hetzner Server Details
- **IP:** 46.224.66.48
- **OS:** Ubuntu 24.04
- **Credentials:** root / jvN9RqLbnqah3tta3KXv
- **Cost:** €15-20/month

### Domain Configuration
- **Primary:** shopfloor-copilot.com
- **Secondary:** opc-studio.com
- **Registrar:** Aruba.it
- **SSL:** Let's Encrypt (valid until March 20, 2026)
- **DNS:** A records configured for @ and www

### Docker Services
1. **shopfloor** - Main application (port 8502)
2. **opc-studio** - OPC UA demo (port 8503)
3. **postgres** - Database (max_connections=300)
4. **chroma** - Vector database (port 8000)
5. **ollama** - LLM service (port 11434)
6. **opc-demo** - Simulated OPC server

### Database Configuration
```yaml
POSTGRES_HOST: postgres
POSTGRES_PASSWORD: XCukqj1dHIN52PewUi0hJVKArpO9gWzQ
POSTGRES_DB: shopfloor_db

Connection Pooling:
- pool_size: 10 per worker
- max_overflow: 20
- pool_recycle: 3600 seconds
- pool_pre_ping: true
- Supports ~30 concurrent users (4 uvicorn workers)
```

---

## 3. Recent Fixes & Improvements

### ✅ Database Connection Issues (Dec 18-19)
**Problem:** Connection refused to 127.0.0.1  
**Solution:** Created `docker-compose.override.yml` with correct `POSTGRES_HOST=postgres`  
**Files Changed:** 
- Added `docker-compose.override.yml` (server-only, in .gitignore)
- Added `psycopg2-binary==2.9.9` to requirements.txt

### ✅ SQL INTERVAL Parameter Binding (Dec 19)
**Problem:** Queries with `INTERVAL ':days days'` returning empty results  
**Solution:** Changed to f-strings: `INTERVAL '{days} days'`  
**Files Fixed:**
- `apps/shopfloor_copilot/screens/production_lines.py` (lines 47, 159)

### ✅ Connection Pooling (Dec 19)
**Problem:** "too many clients already" error  
**Solution:** 
- Increased PostgreSQL `max_connections` to 300
- Added SQLAlchemy connection pooling
**Files Changed:**
- `apps/shopfloor_copilot/routers/oee_analytics.py`
- `docker-compose.override.yml`

### ✅ Empty Dashboards (Dec 19)
**Problem:** No data showing in Live Monitoring and Production Lines  
**Solution:** 
- Created `scripts/generate_live_data.py`
- Installed hourly cron job for automated data generation
- Generates realistic OEE data for current shift (M/A/N)
**Data Populated:**
- 11 production lines
- 33 stations (3 per line)
- Shift detection (M: 6-14, A: 14-22, N: 22-6)
- Auto-cleanup: deletes records >45 days old

### ✅ DNS Configuration (Dec 19)
**Problem:** Domains showing Aruba parking pages  
**Solution:**
- Re-added A records in Aruba.it control panel
- Disabled domain redirects
- Flushed DNS cache
- Verified SSL certificates

### ✅ PDF Export Failure (Dec 20)
**Problem:** "Export PDF" button not working in Production Lines  
**Root Cause:** Library incompatibility
- WeasyPrint 62.3 has transform() bug
- pydyf 0.12.1 incompatible with WeasyPrint 60.2
**Solution:**
- Downgraded `weasyprint` to 60.2
- Downgraded `pydyf` to 0.9.0
- Restarted container to reload modules
**Files Changed:**
- `requirements.txt` (pinned versions)

---

## 4. Automated Tasks (Cron)

### Hourly Data Generation
```bash
0 * * * * cd /opt/shopfloor/rag-suite/scripts && \
  POSTGRES_HOST=localhost POSTGRES_PASSWORD=XCukqj1dHIN52PewUi0hJVKArpO9gWzQ \
  python3 generate_live_data.py >> /var/log/shopfloor-datagen.log 2>&1
```
**Purpose:** Generates realistic OEE data for current shift  
**Tables Updated:** `oee_line_shift`, `oee_station_shift`

### Health Checks (Every 5 minutes)
```bash
*/5 * * * * curl -f http://localhost:8502/ > /dev/null 2>&1 || \
  docker compose -f /opt/shopfloor/rag-suite/docker-compose.prod.yml restart shopfloor
```

### Daily Backups (2 AM)
```bash
0 2 * * * /opt/shopfloor/rag-suite/scripts/backup_databases.sh
```
**Backup Locations:**
- PostgreSQL: `/opt/shopfloor/backups/postgres/`
- ChromaDB: `/opt/shopfloor/backups/chroma/`
- Retention: 7 days

### Weekly Docker Cleanup (Sunday 3 AM)
```bash
0 3 * * 0 docker system prune -af --volumes
```

### Monthly SSL Renewal Check
```bash
0 0 1 * * certbot renew --quiet
```

---

## 5. Current Application Status

### ✅ Working Features
- **Live Monitoring Dashboard** - Real-time OEE metrics per shift
- **Production Lines Dashboard** - 11 lines with 30-day trends
- **Station Heatmap** - 33 stations color-coded by performance
- **CSV Export** - Production lines data export
- **PDF Export** - Production lines report with metrics and issues
- **Automated Data Generation** - Hourly updates for current shift
- **Multi-user Support** - ~30 concurrent users via connection pooling
- **SSL/HTTPS** - Valid certificates, secure connections

### 📊 Database Tables
- **oee_line_shift:** 1023 records (11 lines × 3 shifts × 31 days)
- **oee_station_shift:** ~3069 records (33 stations)
- **oee_downtime_events:** 4410 records

### 🔧 Technical Stack Versions
```txt
Python: 3.11
FastAPI: 0.115.2
NiceGUI: 2.5.0
PostgreSQL: 16
SQLAlchemy: 2.0.36
psycopg2-binary: 2.9.9
ChromaDB: 0.5.20
Ollama: llama3.1:8b
WeasyPrint: 60.2
pydyf: 0.9.0
```

---

## 6. File Structure (Key Files)

```
rag-suite/
├── apps/
│   └── shopfloor_copilot/
│       ├── main.py                    # Application entry point
│       ├── ui.py                      # Main UI layout
│       ├── routers/
│       │   ├── oee_analytics.py       # OEE API endpoints (connection pooling)
│       │   ├── ask.py                 # RAG Q&A endpoints
│       │   ├── ingest.py              # Document ingestion
│       │   ├── export.py              # Export endpoints
│       │   └── kpi.py                 # KPI endpoints
│       └── screens/
│           ├── production_lines.py    # Production dashboard (INTERVAL fix, PDF export)
│           ├── kpi_dashboard_interactive.py
│           ├── operations_dashboard.py
│           └── ...
├── packages/
│   ├── core_rag/                      # RAG functionality
│   ├── core_ingest/                   # Document ingestion
│   ├── export_utils/
│   │   ├── csv_export.py              # CSV generation
│   │   └── pdf_export.py              # PDF generation (WeasyPrint)
│   └── tools/
│       ├── sqlkpi.py                  # SQL KPI queries
│       └── oee_sql_tool.py            # OEE database operations
├── scripts/
│   ├── generate_live_data.py          # Hourly data generation
│   ├── simulate_plant_history.py      # Historical data (30 days)
│   └── backup_databases.sh            # Daily backups
├── docker-compose.yml                 # Base configuration
├── docker-compose.override.yml        # Production config (server-only, .gitignore)
├── requirements.txt                   # Python dependencies
└── docs/
    ├── DEPLOYMENT_NOTES.md            # Deployment workflow
    ├── REPORTING.md                   # Reporting features
    └── SIEMENS_DEMO.md                # Demo scenarios
```

---

## 7. Key Learnings & Best Practices

### PostgreSQL Parameter Binding
❌ **Don't:** `INTERVAL ':days days'` with parameters  
✅ **Do:** `INTERVAL '{days} days'` with f-strings  
Parameter binding doesn't work inside PostgreSQL string literals.

### WeasyPrint Compatibility
- WeasyPrint 60.2 requires pydyf <0.10
- WeasyPrint 62.3/61.2 have transform() bugs
- Always pin compatible versions in requirements.txt

### Docker Module Reloading
After `pip install` inside container, must restart container for Python to reload modules:
```bash
docker compose -f docker-compose.prod.yml restart shopfloor
```

### Connection Pooling Configuration
For 4 uvicorn workers with 10+20 pool configuration:
- Max theoretical connections: 4 × (10 + 20) = 120
- Set PostgreSQL max_connections to 300 for safety margin
- Supports ~30 concurrent users

---

## 8. Next Steps & Roadmap

### Phase 5 (Future Features)
- [ ] Real-time WebSocket updates for dashboards
- [ ] Push notifications for critical alerts
- [ ] User authentication and RBAC
- [ ] SSO integration (LDAP/Azure AD)
- [ ] Advanced predictive maintenance ML models
- [ ] Mobile responsive design improvements

### Pending User Acceptance Testing
- ✅ Live Monitoring
- ✅ Production Lines
- ✅ Station Heatmap
- ✅ CSV Export
- ✅ PDF Export
- ✅ AI Diagnostics (Sprint 3) - `/api/diagnostics/explain` endpoint live
- ⏳ KPI Dashboard (may need INTERVAL fixes)
- ⏳ Predictive Maintenance
- ⏳ Shift Handover
- ⏳ Root Cause Analysis
- ⏳ 5 Whys Analysis
- ⏳ Comparative Analytics

### Potential INTERVAL Fixes Needed
Check these files if dashboards show empty data:
- `apps/shopfloor_copilot/screens/kpi_dashboard_interactive.py` (7 occurrences)
- `apps/shopfloor_copilot/screens/station_heatmap.py` (1 occurrence)

---

## 9. Troubleshooting Commands

### Check Application Status
```bash
ssh root@46.224.66.48
docker ps
docker logs shopfloor-copilot --tail 50
```

### Check Database Connections
```bash
docker exec postgres psql -U postgres -d shopfloor_db -c \
  "SELECT count(*) FROM pg_stat_activity;"
```

### View Live Data Generation
```bash
tail -f /var/log/shopfloor-datagen.log
```

### Verify Data in Database
```bash
docker exec postgres psql -U postgres -d shopfloor_db -c \
  "SELECT COUNT(*) FROM oee_line_shift;"
```

### Check Cron Jobs
```bash
crontab -l
```

### Manual Data Generation
```bash
cd /opt/shopfloor/rag-suite/scripts
POSTGRES_HOST=localhost POSTGRES_PASSWORD=XCukqj1dHIN52PewUi0hJVKArpO9gWzQ \
  python3 generate_live_data.py
```

### Restart Services
```bash
cd /opt/shopfloor/rag-suite
docker compose -f docker-compose.prod.yml restart shopfloor
docker compose -f docker-compose.prod.yml restart postgres
```

---

## 10. Important Notes

### Security
- PostgreSQL password stored in `docker-compose.override.yml` (not in git)
- Server credentials: root/jvN9RqLbnqah3tta3KXv
- SSL certificates auto-renew monthly
- Database backups encrypted and rotated (7-day retention)

### Performance
- Connection pooling supports ~30 concurrent users
- Automated data generation every hour (minimal overhead)
- Docker cleanup weekly to prevent disk bloat
- Health checks every 5 minutes with auto-restart

### Monitoring
- Application logs: `docker logs shopfloor-copilot`
- Data generation logs: `/var/log/shopfloor-datagen.log`
- PostgreSQL logs: `docker logs postgres`
- Nginx access logs: `/var/log/nginx/access.log`

---

## 11. Contact & Access

**Production URL:** https://shopfloor-copilot.com  
**Server IP:** 46.224.66.48  
**SSH Access:** `ssh root@46.224.66.48` (password: jvN9RqLbnqah3tta3KXv)  
**Domain Registrar:** Aruba.it (user credentials with Davide)  
**SSL Provider:** Let's Encrypt (auto-renewal configured)

---

## Summary

The Shopfloor Copilot application is **fully deployed and operational** on Hetzner Cloud with:
- ✅ 11 production lines with real-time OEE monitoring
- ✅ Automated hourly data generation for current shift
- ✅ CSV and PDF export functionality (WeasyPrint 60.2 + pydyf 0.9.0)
- ✅ Connection pooling for ~30 concurrent users
- ✅ SSL certificates with auto-renewal
- ✅ Daily backups with 7-day retention
- ✅ Health checks with auto-restart

**Recent Sprint (Dec 18-20):** Completed full deployment, fixed database connectivity, SQL parameter binding, connection pooling, automated data generation, DNS configuration, and PDF export compatibility issues. **Sprint 3 (AI Diagnostics) deployed and operational.**

**Current Status:** All core features working including AI-grounded diagnostics. Ready for comprehensive user acceptance testing.
