#!/bin/bash
# Restore script for Shopfloor Copilot
# Usage: ./restore.sh BACKUP_DATE
# Example: ./restore.sh 20251218_020000

set -e

BACKUP_DATE="${1}"
BACKUP_DIR="${HOME}/shopfloor-deploy/backups"

if [ -z "${BACKUP_DATE}" ]; then
    echo "Usage: $0 BACKUP_DATE"
    echo ""
    echo "Available backups:"
    ls -1 "${BACKUP_DIR}"/postgres_*.sql.gz | sed 's/.*postgres_\(.*\)\.sql\.gz/\1/' | sort -r | head -10
    exit 1
fi

echo "🔄 Starting restore from backup: ${BACKUP_DATE}"
echo ""
read -p "⚠️  This will overwrite current data. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 1
fi

# Check if backup files exist
POSTGRES_BACKUP="${BACKUP_DIR}/postgres_${BACKUP_DATE}.sql.gz"
CHROMA_BACKUP="${BACKUP_DIR}/chroma_${BACKUP_DATE}.tar.gz"
CONFIG_BACKUP="${BACKUP_DIR}/config_${BACKUP_DATE}.tar.gz"

if [ ! -f "${POSTGRES_BACKUP}" ]; then
    echo "❌ PostgreSQL backup not found: ${POSTGRES_BACKUP}"
    exit 1
fi

# Stop services
echo "🛑 Stopping services..."
cd "${HOME}/rag-suite"
docker compose down

# Restore PostgreSQL
echo "📥 Restoring PostgreSQL database..."
docker compose up -d postgres
sleep 10
gunzip < "${POSTGRES_BACKUP}" | docker exec -i shopfloor-postgres psql -U shopfloor shopfloor_mes
echo "✓ PostgreSQL restored"

# Restore ChromaDB
if [ -f "${CHROMA_BACKUP}" ]; then
    echo "📥 Restoring ChromaDB..."
    docker compose up -d chroma
    sleep 5
    docker cp "${CHROMA_BACKUP}" shopfloor-chroma:/tmp/chroma_backup.tar.gz
    docker exec shopfloor-chroma tar -xzf /tmp/chroma_backup.tar.gz -C /
    docker exec shopfloor-chroma rm /tmp/chroma_backup.tar.gz
    echo "✓ ChromaDB restored"
else
    echo "⚠️ ChromaDB backup not found, skipping"
fi

# Restore configuration
if [ -f "${CONFIG_BACKUP}" ]; then
    echo "📥 Restoring configuration..."
    tar -xzf "${CONFIG_BACKUP}" -C "${HOME}/shopfloor-deploy"
    echo "✓ Configuration restored"
else
    echo "⚠️ Config backup not found, skipping"
fi

# Restart all services
echo "▶️ Starting all services..."
docker compose up -d
sleep 30

# Verify services
echo "🏥 Verifying services..."
docker compose ps

echo ""
echo "✅ Restore completed successfully!"
echo ""
echo "Next steps:"
echo "1. Verify application: http://localhost:8010/health"
echo "2. Check logs: docker compose logs -f"
echo "3. Test OPC connection"
