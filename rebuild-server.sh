#!/bin/bash
# Rebuild Shopfloor Copilot on Hetzner Server
# Run this script on the server via SSH

echo "🔄 Navigating to application directory..."
cd /opt/shopfloor/rag-suite

echo "🛑 Stopping all services..."
docker compose down

echo "🏗️ Rebuilding Docker images (this will take 5-10 minutes)..."
docker compose build --no-cache

echo "🚀 Starting services..."
docker compose up -d

echo "✅ Waiting 10 seconds for services to start..."
sleep 10

echo "📊 Checking service status..."
docker compose ps

echo ""
echo "🎉 Done! Access your app at:"
echo "   http://46.224.66.48:8010"
echo ""
echo "📝 To view logs:"
echo "   docker compose logs -f shopfloor"
