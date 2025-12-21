#!/bin/bash
# ============================================================================
# backup-database.sh - Automatic PostgreSQL Backup
# ============================================================================
# Purpose: Create daily backups with retention policy
# Usage: ./scripts/backup-database.sh
# Cron: 0 2 * * * /opt/shopfloor/rag-suite/scripts/backup-database.sh
# ============================================================================

set -e

BACKUP_DIR="/opt/shopfloor/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ragdb_backup_$TIMESTAMP.sql"
RETENTION_DAYS=7

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "🔄 Starting database backup..."
echo "📅 Timestamp: $TIMESTAMP"

# Dump database (schema + data)
docker exec shopfloor-postgres pg_dump -U postgres -d ragdb --encoding=UTF8 > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

# Get file size
SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✅ Backup completed: $BACKUP_FILE ($SIZE)"

# Delete backups older than retention period
echo "🧹 Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "ragdb_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "ragdb_backup_*.sql.gz" | wc -l)
echo "📦 Total backups: $BACKUP_COUNT"

# Keep a "latest" symlink
ln -sf "$BACKUP_FILE" "$BACKUP_DIR/ragdb_latest.sql.gz"

echo "✅ Backup process complete!"
