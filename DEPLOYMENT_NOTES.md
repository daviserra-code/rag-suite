# Deployment Notes - Hetzner Production

## Server Configuration Files (Not in Git)

These files exist **only on the Hetzner server** and are **NOT tracked by git**:

### `/opt/shopfloor/rag-suite/docker-compose.override.yml`
```yaml
services:
  shopfloor:
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=ragdb
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=XCukqj1dHIN52PewUi0hJVKArpO9gWzQ
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=ragdb
      - DB_USER=postgres
      - DB_PASSWORD=XCukqj1dHIN52PewUi0hJVKArpO9gWzQ
      - SQLALCHEMY_POOL_SIZE=10
      - SQLALCHEMY_MAX_OVERFLOW=20
      - SQLALCHEMY_POOL_RECYCLE=3600
      - SQLALCHEMY_POOL_PRE_PING=true

  postgres:
    command: postgres -c max_connections=300 -c shared_buffers=256MB
```

**Purpose**: 
- Sets database connection environment variables
- Configures PostgreSQL max_connections=300 (supports ~30 concurrent users)
- Enables SQLAlchemy connection pooling

**Important**: This file is in `.gitignore` and will **NOT be overwritten** when you pull from git.

### `/opt/shopfloor/rag-suite/postgres.conf`
Optional PostgreSQL configuration file (currently not used, using command-line args instead).

## Deployment Workflow from GMKtec

When deploying new code from your local machine:

1. **On GMKtec (local)**:
   ```powershell
   cd "C:\Users\Davide\VS-Code Solutions\rag-suite"
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **On Hetzner (SSH)**:
   ```bash
   ssh root@46.224.66.48
   cd /opt/shopfloor/rag-suite
   git pull origin main
   docker compose -f docker-compose.prod.yml build --no-cache
   docker compose -f docker-compose.prod.yml up -d
   ```

3. **Verify**:
   ```bash
   docker ps
   docker logs shopfloor-copilot
   ```

## What Gets Preserved

✅ **docker-compose.override.yml** - Stays on server, not overwritten
✅ **postgres.conf** - Stays on server, not overwritten  
✅ **.env.prod** - Server-specific credentials (not in git)
✅ **PostgreSQL data** - Persisted in Docker volume `pgdata`
✅ **ChromaDB data** - Persisted in Docker volume `chroma_data`
✅ **Cron jobs** - Installed on server, not affected by code updates

## What Gets Updated

🔄 **Python code** - All `.py` files in apps/, packages/
🔄 **docker-compose.prod.yml** - Base configuration
🔄 **Dockerfile** - Container build instructions
🔄 **requirements.txt** - Python dependencies

## Database Connection Pooling

The code in `apps/shopfloor_copilot/routers/oee_analytics.py` now includes connection pooling configuration that reads from environment variables set in `docker-compose.override.yml`:

- `SQLALCHEMY_POOL_SIZE=10` - Base connection pool per worker
- `SQLALCHEMY_MAX_OVERFLOW=20` - Extra connections when needed
- `SQLALCHEMY_POOL_RECYCLE=3600` - Recycle connections every hour
- `SQLALCHEMY_POOL_PRE_PING=true` - Test connections before use

With 4 uvicorn workers, this supports approximately **30 concurrent users** without "too many connections" errors.

## Quick Reference

### Restart Services
```bash
cd /opt/shopfloor/rag-suite
docker compose -f docker-compose.prod.yml restart
```

### Rebuild After Code Changes
```bash
cd /opt/shopfloor/rag-suite
git pull
docker compose -f docker-compose.prod.yml build --no-cache shopfloor
docker compose -f docker-compose.prod.yml up -d shopfloor
```

### Check Database Connections
```bash
docker exec shopfloor-postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
docker exec shopfloor-postgres psql -U postgres -c "SHOW max_connections;"
```

### View Logs
```bash
docker logs -f shopfloor-copilot
docker logs -f shopfloor-postgres
```

### Manual Backup
```bash
cd /opt/shopfloor/rag-suite
./scripts/backup.sh
```

### Check Cron Jobs
```bash
crontab -l
tail -f /var/log/shopfloor-health.log
tail -f /var/log/shopfloor-datagen.log
```

### View Live Data Generation
```bash
# Check if data is being generated
docker exec shopfloor-postgres psql -U postgres -d ragdb -c "SELECT date, shift, COUNT(*) FROM oee_line_shift WHERE date = CURRENT_DATE GROUP BY date, shift ORDER BY shift DESC;"

# View latest records
docker exec shopfloor-postgres psql -U postgres -d ragdb -c "SELECT line_id, date, shift, oee FROM oee_line_shift WHERE date = CURRENT_DATE ORDER BY line_id LIMIT 5;"
```

## Production URLs

- **Main App**: https://shopfloor-copilot.com
- **OPC Studio**: https://opc-studio.com
- **Server IP**: 46.224.66.48
- **Hetzner Console**: https://console.hetzner.cloud

## Automated Tasks

- **Live Data Generation**: Every hour (generates current shift OEE data)
- **Backups**: Daily at 2:00 AM (7-day retention)
- **Health Checks**: Every 5 minutes
- **Docker Cleanup**: Weekly on Sundays at 3:00 AM
- **Log Rotation**: Daily at 4:00 AM
- **SSL Renewal**: Monthly check on 1st at 5:00 AM

### Live Data Generation

The `generate_live_data.py` script runs hourly to keep dashboards fresh:

- **Schedule**: Top of every hour (00 minutes)
- **Purpose**: Generates realistic OEE data for current shift
- **Shifts**: 
  - Morning (M): 6:00-14:00
  - Afternoon (A): 14:00-22:00
  - Night (N): 22:00-6:00
- **Scope**: Updates all 11 production lines + 33 stations
- **Data Cleanup**: Automatically removes records older than 45 days
- **Log**: `/var/log/shopfloor-datagen.log`

**Manual run:**
```bash
cd /opt/shopfloor/rag-suite/scripts
POSTGRES_HOST=localhost POSTGRES_PASSWORD=XCukqj1dHIN52PewUi0hJVKArpO9gWzQ python3 generate_live_data.py
```

## Support & Troubleshooting

If you encounter issues after deployment:

1. Check container status: `docker ps`
2. Check logs: `docker logs shopfloor-copilot`
3. Check database: `docker exec shopfloor-postgres psql -U postgres -c "SELECT version();"`
4. Restart if needed: `docker compose -f docker-compose.prod.yml restart`

## Production Fixes Applied

### SQL INTERVAL Parameter Binding Fix

**Problem**: SQL queries with `INTERVAL ':days days'` using parameter binding were returning empty results.

**Solution**: Changed from parameter binding to f-string formatting for INTERVAL clauses:

**Files Fixed:**
- `apps/shopfloor_copilot/screens/production_lines.py`
  - `get_production_lines_summary()`: Changed to `f"... INTERVAL '{days} days'"`
  - `get_line_trend()`: Changed to `f"... INTERVAL '{days} days'"`
- `apps/shopfloor_copilot/routers/oee_analytics.py`: Added connection pooling

**Other files needing same fix (if used):**
- `apps/shopfloor_copilot/screens/kpi_dashboard_interactive.py` (7 occurrences)
- `apps/shopfloor_copilot/screens/station_heatmap.py` (1 occurrence)

### Connection Pooling Configuration

**Problem**: "Too many connections" error with multiple concurrent users.

**Solution**: 
1. Increased PostgreSQL `max_connections` from 100 to 300
2. Added SQLAlchemy connection pooling:
   - `pool_size=10` per worker
   - `max_overflow=20` extra connections
   - `pool_recycle=3600` (1 hour)
   - `pool_pre_ping=true` (test before use)

**Configuration in `docker-compose.override.yml`:**
```yaml
services:
  shopfloor:
    environment:
      - SQLALCHEMY_POOL_SIZE=10
      - SQLALCHEMY_MAX_OVERFLOW=20
      - SQLALCHEMY_POOL_RECYCLE=3600
      - SQLALCHEMY_POOL_PRE_PING=true

  postgres:
    command: postgres -c max_connections=300 -c shared_buffers=256MB
```

**Supports**: ~30 concurrent users with 4 uvicorn workers

### Live Data Generation

**Problem**: Dashboards showed no data because historical data was outdated (not including current date).

**Solution**: Created `scripts/generate_live_data.py` to automatically generate fresh OEE data every hour.

---

**Last Updated**: December 20, 2025
**Server**: Hetzner Cloud (46.224.66.48)
**Domains**: shopfloor-copilot.com, opc-studio.com
