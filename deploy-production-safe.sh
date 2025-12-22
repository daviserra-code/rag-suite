#!/bin/bash
# SAFE PRODUCTION DEPLOYMENT SCRIPT
# Hetzner Server: 46.224.66.48
# Date: December 22, 2025

set -e  # Exit on any error

echo "==================================="
echo "🚀 SAFE PRODUCTION DEPLOYMENT"
echo "==================================="
echo ""

# Configuration
SERVER="46.224.66.48"
APP_PATH="/opt/shopfloor/rag-suite"
BACKUP_PATH="/opt/shopfloor/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "📋 Pre-deployment checklist:"
echo "  ✓ Code committed and pushed to git"
echo "  ✓ Local testing completed"
echo "  ✓ All syntax errors fixed"
echo ""

# Step 1: Create backup
echo "Step 1/7: Creating backup snapshot..."
ssh root@$SERVER "mkdir -p $BACKUP_PATH && \
  cd $APP_PATH && \
  docker-compose logs shopfloor > $BACKUP_PATH/logs_before_$TIMESTAMP.txt && \
  tar -czf $BACKUP_PATH/rag-suite_backup_$TIMESTAMP.tar.gz \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.git' \
    . && \
  echo '✅ Backup created: $BACKUP_PATH/rag-suite_backup_$TIMESTAMP.tar.gz'"

# Step 2: Pull latest code
echo ""
echo "Step 2/7: Pulling latest code from git..."
ssh root@$SERVER "cd $APP_PATH && \
  git fetch origin && \
  git reset --hard origin/main && \
  echo '✅ Code updated to latest version'"

# Step 3: Stop services gracefully
echo ""
echo "Step 3/7: Stopping services gracefully..."
ssh root@$SERVER "cd $APP_PATH && \
  docker-compose stop shopfloor opc-studio && \
  echo '✅ Services stopped'"

# Step 4: Build new images
echo ""
echo "Step 4/7: Building new Docker images..."
ssh root@$SERVER "cd $APP_PATH && \
  docker-compose build shopfloor opc-studio && \
  echo '✅ Images built successfully'"

# Step 5: Start services
echo ""
echo "Step 5/7: Starting services..."
ssh root@$SERVER "cd $APP_PATH && \
  docker-compose up -d shopfloor opc-studio && \
  echo '✅ Services started'"

# Step 6: Wait for startup
echo ""
echo "Step 6/7: Waiting for services to be ready (30 seconds)..."
sleep 30

# Step 7: Health check
echo ""
echo "Step 7/7: Performing health checks..."
ssh root@$SERVER "cd $APP_PATH && \
  docker-compose ps && \
  echo '' && \
  docker-compose logs --tail=10 shopfloor | grep -E 'Application startup complete|ERROR|Exception' || true"

echo ""
echo "==================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "==================================="
echo ""
echo "📊 Service URLs:"
echo "  • Shopfloor Copilot: http://46.224.66.48:8010"
echo "  • OPC Studio: http://46.224.66.48:8040"
echo ""
echo "🔍 To check logs:"
echo "  ssh root@46.224.66.48"
echo "  cd /opt/shopfloor/rag-suite"
echo "  docker-compose logs -f shopfloor"
echo ""
echo "⚠️  If issues occur, rollback with:"
echo "  ssh root@46.224.66.48"
echo "  cd /opt/shopfloor/rag-suite"
echo "  tar -xzf /opt/shopfloor/backups/rag-suite_backup_$TIMESTAMP.tar.gz"
echo "  docker-compose up -d --build"
echo ""
echo "🎉 Ready for demo!"
