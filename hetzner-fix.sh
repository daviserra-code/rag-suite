#!/bin/bash
# Quick fix script for Hetzner - Restore database and restart services
# Run this on your Hetzner server

set -e

echo "═══════════════════════════════════════════════════════"
echo "  Shopfloor Copilot - Hetzner Quick Fix"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check if database backup exists
if [ ! -f "ragdb_backup_utf8.sql" ]; then
    echo "❌ Database backup file not found: ragdb_backup_utf8.sql"
    echo "   Upload the backup file first, then run this script again"
    exit 1
fi

echo "✅ Database backup file found"
echo ""

# Stop all services
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Stopping services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose down
echo "✅ Services stopped"
echo ""

# Start only PostgreSQL first
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Starting PostgreSQL..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose up -d postgres
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Wait for PostgreSQL to be healthy
MAX_WAIT=30
COUNTER=0
while [ $COUNTER -lt $MAX_WAIT ]; do
    if docker compose ps postgres | grep -q "healthy"; then
        echo "✅ PostgreSQL is healthy"
        break
    fi
    echo "   Waiting... ($COUNTER/$MAX_WAIT)"
    sleep 2
    COUNTER=$((COUNTER + 1))
done

if [ $COUNTER -eq $MAX_WAIT ]; then
    echo "❌ PostgreSQL failed to become healthy"
    echo "   Check logs: docker compose logs postgres"
    exit 1
fi

echo ""

# Check if database already has data
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Checking existing data..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
EXISTING_ROWS=$(docker compose exec -T postgres psql -U postgres -d ragdb -t -c "SELECT COUNT(*) FROM oee_line_shift;" 2>/dev/null | xargs || echo "0")
echo "Current row count: $EXISTING_ROWS"

if [ "$EXISTING_ROWS" -gt 0 ]; then
    echo "⚠️  Database already contains $EXISTING_ROWS rows"
    read -p "Do you want to restore anyway? This will add/update data. (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping database restore"
    else
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Step 4: Restoring database..."
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        cat ragdb_backup_utf8.sql | docker compose exec -T postgres psql -U postgres -d ragdb
        echo "✅ Database restored"
    fi
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 4: Restoring database..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat ragdb_backup_utf8.sql | docker compose exec -T postgres psql -U postgres -d ragdb
    echo "✅ Database restored"
fi

echo ""

# Verify restoration
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Verifying data..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
NEW_ROWS=$(docker compose exec -T postgres psql -U postgres -d ragdb -t -c "SELECT COUNT(*) FROM oee_line_shift;" | xargs)
echo "✅ Total rows in oee_line_shift: $NEW_ROWS"

LATEST=$(docker compose exec -T postgres psql -U postgres -d ragdb -t -c "SELECT MAX(shift_date) FROM oee_line_shift;" | xargs)
echo "✅ Latest data date: $LATEST"

LINES=$(docker compose exec -T postgres psql -U postgres -d ragdb -t -c "SELECT COUNT(DISTINCT line_id) FROM oee_line_shift;" | xargs)
echo "✅ Production lines: $LINES"

echo ""

# Start all services
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Starting all services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Use production compose file if it exists
if [ -f "docker-compose.prod.yml" ]; then
    docker compose -f docker-compose.prod.yml --profile hetzner up -d
    echo "✅ Services started with production profile"
else
    docker compose --profile hetzner up -d
    echo "✅ Services started"
fi

echo ""
echo "⏳ Waiting for services to start..."
sleep 15

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7: Health check..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check shopfloor health
if curl -s http://localhost:8010/health > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8010/health)
    echo "✅ Shopfloor Copilot: $HEALTH"
else
    echo "⚠️  Shopfloor Copilot not responding yet (may need more time)"
fi

# Check OPC Studio health
if curl -s http://localhost:8040/health > /dev/null 2>&1; then
    OPC_HEALTH=$(curl -s http://localhost:8040/health)
    echo "✅ OPC Studio: $OPC_HEALTH"
else
    echo "⚠️  OPC Studio not responding yet (may need more time)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 8: Container status..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose ps

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ Fix Complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Your application should now be accessible with data."
echo ""
echo "Useful commands:"
echo "  - View logs: docker compose logs -f"
echo "  - Check status: docker compose ps"
echo "  - Restart a service: docker compose restart shopfloor"
echo ""
echo "If you still don't see data, check browser cache:"
echo "  - Hard refresh: Ctrl+Shift+R (Chrome/Firefox)"
echo "  - Clear cache and reload"
echo ""
