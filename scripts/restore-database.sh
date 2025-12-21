#!/bin/bash
# ============================================================================
# restore-database.sh - Restore PostgreSQL from Backup
# ============================================================================
# Purpose: Restore database from backup file
# Usage: ./scripts/restore-database.sh <backup_file>
# Example: ./scripts/restore-database.sh /opt/shopfloor/backups/ragdb_backup_20251221_020000.sql.gz
# ============================================================================

set -e

if [ -z "$1" ]; then
    echo "❌ Error: Backup file not specified"
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh /opt/shopfloor/backups/ragdb_backup_*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will OVERWRITE the current database!"
echo "📁 Backup file: $BACKUP_FILE"
echo ""
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Restore cancelled"
    exit 0
fi

echo "🔄 Restoring database..."

# Decompress if needed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "📦 Decompressing backup..."
    gunzip -c "$BACKUP_FILE" | docker exec -i shopfloor-postgres psql -U postgres -d ragdb
else
    docker exec -i shopfloor-postgres psql -U postgres -d ragdb < "$BACKUP_FILE"
fi

echo "✅ Database restored successfully!"
echo "🔄 Restarting services..."
cd /opt/shopfloor/rag-suite
docker compose restart shopfloor data-simulator

echo "✅ Restore complete!"
