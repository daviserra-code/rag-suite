#!/bin/bash
# Backup script for Shopfloor Copilot
# Run daily via cron: 0 2 * * * /home/deploy/shopfloor-deploy/scripts/backup.sh

set -e

# Configuration
BACKUP_DIR="${HOME}/shopfloor-deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "🗄️ Starting backup: ${DATE}"

# Backup PostgreSQL
echo "📦 Backing up PostgreSQL database..."
if docker ps | grep -q shopfloor-postgres; then
    docker exec shopfloor-postgres pg_dump -U shopfloor shopfloor_mes | gzip > "${BACKUP_DIR}/postgres_${DATE}.sql.gz"
    echo "✓ PostgreSQL backup: ${BACKUP_DIR}/postgres_${DATE}.sql.gz"
else
    echo "⚠️ PostgreSQL container not running, skipping database backup"
fi

# Backup ChromaDB
echo "📦 Backing up ChromaDB..."
if docker ps | grep -q shopfloor-chroma; then
    docker exec shopfloor-chroma tar -czf /tmp/chroma_backup.tar.gz /chroma/data 2>/dev/null || true
    docker cp shopfloor-chroma:/tmp/chroma_backup.tar.gz "${BACKUP_DIR}/chroma_${DATE}.tar.gz"
    docker exec shopfloor-chroma rm /tmp/chroma_backup.tar.gz
    echo "✓ ChromaDB backup: ${BACKUP_DIR}/chroma_${DATE}.tar.gz"
else
    echo "⚠️ ChromaDB container not running, skipping"
fi

# Backup configuration files
echo "📦 Backing up configuration..."
tar -czf "${BACKUP_DIR}/config_${DATE}.tar.gz" \
    -C "${HOME}/shopfloor-deploy" \
    config/ \
    2>/dev/null || true
echo "✓ Config backup: ${BACKUP_DIR}/config_${DATE}.tar.gz"

# Backup OPC Studio mappings
echo "📦 Backing up OPC Studio mappings..."
if [ -d "${HOME}/rag-suite/opc-studio/config" ]; then
    tar -czf "${BACKUP_DIR}/opc_mappings_${DATE}.tar.gz" \
        -C "${HOME}/rag-suite" \
        opc-studio/config/ \
        2>/dev/null || true
    echo "✓ OPC mappings backup: ${BACKUP_DIR}/opc_mappings_${DATE}.tar.gz"
fi

# Clean old backups
echo "🧹 Cleaning old backups (retention: ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "*.gz" -type f -mtime +${RETENTION_DAYS} -delete
echo "✓ Old backups cleaned"

# Calculate backup sizes
echo ""
echo "📊 Backup Summary:"
echo "  Date: ${DATE}"
echo "  Location: ${BACKUP_DIR}"
echo ""
echo "  Files created:"
ls -lh "${BACKUP_DIR}"/*_${DATE}* 2>/dev/null || echo "  (none)"
echo ""
echo "  Total backup size:"
du -sh "${BACKUP_DIR}"

# Optional: Upload to remote storage
# Uncomment and configure for remote backups
# if command -v rclone &> /dev/null; then
#     echo "☁️ Uploading to remote storage..."
#     rclone copy "${BACKUP_DIR}" remote:shopfloor-backups/
#     echo "✓ Remote backup complete"
# fi

echo ""
echo "✅ Backup completed successfully!"
