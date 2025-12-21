# Database Backup & Restore Guide

## Automatic Backups

**Location:** `/opt/shopfloor/backups/`  
**Schedule:** Daily at 2:00 AM (configured via cron)  
**Retention:** 7 days  
**Format:** Compressed SQL (gzip)

### Setup Automatic Backups

```bash
# On Hetzner server
ssh root@46.224.66.48

# Make scripts executable
cd /opt/shopfloor/rag-suite
chmod +x scripts/backup-database.sh
chmod +x scripts/restore-database.sh

# Add to crontab
crontab -e

# Add this line:
0 2 * * * /opt/shopfloor/rag-suite/scripts/backup-database.sh >> /var/log/shopfloor-backup.log 2>&1
```

### Manual Backup

```bash
cd /opt/shopfloor/rag-suite
./scripts/backup-database.sh
```

This creates: `/opt/shopfloor/backups/ragdb_backup_YYYYMMDD_HHMMSS.sql.gz`

---

## Restore Database

### List Available Backups

```bash
ls -lh /opt/shopfloor/backups/
```

### Restore from Backup

```bash
cd /opt/shopfloor/rag-suite
./scripts/restore-database.sh /opt/shopfloor/backups/ragdb_backup_20251221_020000.sql.gz
```

⚠️ **WARNING:** This will overwrite the current database!

### Quick Restore (Latest Backup)

```bash
cd /opt/shopfloor/rag-suite
./scripts/restore-database.sh /opt/shopfloor/backups/ragdb_latest.sql.gz
```

---

## Emergency Backup Before Maintenance

**Always run this before:**
- Updating Docker images
- Modifying database schema
- Running migration scripts
- Deleting volumes (`docker volume rm`)

```bash
# Quick backup with timestamp
docker exec shopfloor-postgres pg_dump -U postgres -d ragdb --encoding=UTF8 | gzip > /opt/shopfloor/backups/emergency_$(date +%Y%m%d_%H%M%S).sql.gz
```

---

## Backup from Local to Hetzner

```bash
# From local machine
docker exec shopfloor-postgres pg_dump -U postgres -d ragdb --encoding=UTF8 | gzip | ssh root@46.224.66.48 "cat > /opt/shopfloor/backups/local_sync_$(date +%Y%m%d_%H%M%S).sql.gz"
```

---

## Download Backup Locally

```bash
# Download latest backup
scp root@46.224.66.48:/opt/shopfloor/backups/ragdb_latest.sql.gz ./
```

---

## Monitoring

Check backup logs:
```bash
tail -f /var/log/shopfloor-backup.log
```

Check disk space:
```bash
df -h /opt/shopfloor/backups
```

---

## Recovery Scenarios

### Scenario 1: Accidental Data Deletion
```bash
# Stop simulator to prevent new data
docker compose stop data-simulator

# Restore from latest backup
./scripts/restore-database.sh /opt/shopfloor/backups/ragdb_latest.sql.gz

# Restart services
docker compose start data-simulator shopfloor
```

### Scenario 2: Corrupted Database
```bash
# Backup current state (even if corrupted)
docker exec shopfloor-postgres pg_dump -U postgres -d ragdb > /tmp/corrupted_db.sql

# Drop and recreate database
docker exec shopfloor-postgres psql -U postgres -c "DROP DATABASE ragdb;"
docker exec shopfloor-postgres psql -U postgres -c "CREATE DATABASE ragdb;"

# Restore from backup
./scripts/restore-database.sh /opt/shopfloor/backups/ragdb_latest.sql.gz
```

### Scenario 3: Full System Rebuild
```bash
# On new server
cd /opt/shopfloor/rag-suite
docker compose up -d postgres

# Wait for PostgreSQL to start
sleep 10

# Restore backup
gunzip -c /path/to/backup.sql.gz | docker exec -i shopfloor-postgres psql -U postgres -d ragdb

# Start all services
docker compose --profile hetzner up -d
```

---

## Best Practices

✅ **DO:**
- Run manual backup before any maintenance
- Test restore procedure monthly
- Monitor backup logs
- Keep 7+ days of backups
- Store backups on separate volume/server

❌ **DON'T:**
- Delete volumes without backup
- Assume backups are working (test them!)
- Store only one backup copy
- Ignore backup failure notifications

---

## Backup Verification

Test backup integrity:
```bash
# Decompress and check SQL syntax
gunzip -c /opt/shopfloor/backups/ragdb_latest.sql.gz | head -100

# Count records in backup
gunzip -c /opt/shopfloor/backups/ragdb_latest.sql.gz | grep "COPY oee_line_shift" | head -1
```

---

**Version:** 1.0  
**Last Updated:** December 21, 2025
