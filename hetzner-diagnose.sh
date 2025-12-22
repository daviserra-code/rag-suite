#!/bin/bash
# Hetzner Troubleshooting Script - Check why data is not visible
# Run this on your Hetzner server: bash hetzner-diagnose.sh

echo "═══════════════════════════════════════════════════════"
echo "  Shopfloor Copilot - Hetzner Diagnostics"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check if docker compose is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

echo "✅ Docker is installed"
docker --version
echo ""

# Check running containers
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Checking Container Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose ps
echo ""

# Check PostgreSQL container
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Checking PostgreSQL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if postgres container exists
if docker compose ps | grep -q postgres; then
    echo "✅ PostgreSQL container exists"
    
    # Check if it's running
    if docker compose ps | grep postgres | grep -q "Up"; then
        echo "✅ PostgreSQL is running"
        
        # Check if it's healthy
        if docker compose ps | grep postgres | grep -q "healthy"; then
            echo "✅ PostgreSQL is healthy"
        else
            echo "⚠️  PostgreSQL is running but not healthy"
            docker compose logs --tail=20 postgres
        fi
        
        # Check data in database
        echo ""
        echo "Checking database content..."
        echo "─────────────────────────────────────────────────────"
        
        # Check oee_line_shift table
        ROW_COUNT=$(docker compose exec -T postgres psql -U postgres -d ragdb -t -c "SELECT COUNT(*) FROM oee_line_shift;" 2>/dev/null | xargs)
        if [ -n "$ROW_COUNT" ]; then
            echo "✅ oee_line_shift table: $ROW_COUNT rows"
            if [ "$ROW_COUNT" -eq 0 ]; then
                echo "❌ DATABASE IS EMPTY - No OEE data"
                echo ""
                echo "   Fix: Restore database from backup"
                echo "   Run: docker compose exec -T postgres psql -U postgres -d ragdb < ragdb_backup_utf8.sql"
            fi
        else
            echo "❌ Cannot query oee_line_shift table"
        fi
        
        # Check v_runtime_kpi view
        VIEW_COUNT=$(docker compose exec -T postgres psql -U postgres -d ragdb -t -c "SELECT COUNT(*) FROM v_runtime_kpi;" 2>/dev/null | xargs)
        if [ -n "$VIEW_COUNT" ]; then
            echo "✅ v_runtime_kpi view: $VIEW_COUNT rows"
        else
            echo "⚠️  v_runtime_kpi view missing or inaccessible"
        fi
        
        # Check latest data timestamp
        LATEST=$(docker compose exec -T postgres psql -U postgres -d ragdb -t -c "SELECT MAX(shift_date) FROM oee_line_shift;" 2>/dev/null | xargs)
        if [ -n "$LATEST" ]; then
            echo "✅ Latest data: $LATEST"
        fi
        
    else
        echo "❌ PostgreSQL container is not running"
        echo "   Status: $(docker compose ps | grep postgres | awk '{print $5, $6, $7}')"
        echo ""
        echo "   Checking logs:"
        docker compose logs --tail=30 postgres
    fi
else
    echo "❌ PostgreSQL container not found in docker compose"
    echo "   Check if postgres service is defined in docker-compose.yml"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Checking Shopfloor Application"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if docker compose ps | grep -q shopfloor; then
    echo "✅ Shopfloor container exists"
    
    if docker compose ps | grep shopfloor | grep -q "Up"; then
        echo "✅ Shopfloor is running"
        
        # Check health endpoint
        HEALTH=$(curl -s http://localhost:8010/health 2>/dev/null)
        if [ -n "$HEALTH" ]; then
            echo "✅ Shopfloor health: $HEALTH"
        else
            echo "❌ Shopfloor health endpoint not responding"
            echo "   Last 20 log lines:"
            docker compose logs --tail=20 shopfloor
        fi
    else
        echo "❌ Shopfloor container not running"
        echo "   Last 30 log lines:"
        docker compose logs --tail=30 shopfloor
    fi
else
    echo "❌ Shopfloor container not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Checking OPC Studio"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if docker compose ps | grep -q opc-studio; then
    echo "✅ OPC Studio container exists"
    
    if docker compose ps | grep opc-studio | grep -q "Up"; then
        echo "✅ OPC Studio is running"
        
        # Check health endpoint
        OPC_HEALTH=$(curl -s http://localhost:8040/health 2>/dev/null)
        if [ -n "$OPC_HEALTH" ]; then
            echo "✅ OPC Studio health: $OPC_HEALTH"
        else
            echo "⚠️  OPC Studio health endpoint not responding"
        fi
    else
        echo "❌ OPC Studio not running"
        docker compose logs --tail=20 opc-studio
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Checking Data Simulator"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if docker compose ps | grep -q data-simulator; then
    echo "✅ Data Simulator container exists"
    
    if docker compose ps | grep data-simulator | grep -q "Up"; then
        echo "✅ Data Simulator is running"
        echo "   Last 10 log lines:"
        docker compose logs --tail=10 data-simulator
    else
        echo "⚠️  Data Simulator not running (this may be expected)"
    fi
else
    echo "ℹ️  Data Simulator not configured (using OPC Studio historian instead)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Environment Variables Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f .env ]; then
    echo "✅ .env file exists"
    echo ""
    echo "Database configuration:"
    grep -E "^(POSTGRES_HOST|POSTGRES_PORT|POSTGRES_USER|POSTGRES_DB|DATABASE_URL)" .env | sed 's/=.*/=***/' || echo "   No database config found"
else
    echo "❌ .env file not found"
    echo "   Create one from .env.hetzner"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. Quick Fix Commands"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "If database is empty, restore from backup:"
echo "  cat ragdb_backup_utf8.sql | docker compose exec -T postgres psql -U postgres -d ragdb"
echo ""
echo "If containers are unhealthy, restart:"
echo "  docker compose restart"
echo ""
echo "If services won't start, check logs:"
echo "  docker compose logs -f"
echo ""
echo "To rebuild and restart everything:"
echo "  docker compose down && docker compose up -d --build"
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Diagnostics Complete"
echo "═══════════════════════════════════════════════════════"
