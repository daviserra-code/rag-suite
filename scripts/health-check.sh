#!/bin/bash
# Health check script for Shopfloor Copilot
# Run via cron: */5 * * * * /home/deploy/shopfloor-deploy/scripts/health-check.sh

set -e

# Configuration
ALERT_EMAIL="admin@yourcompany.com"
SLACK_WEBHOOK=""  # Optional: Add Slack webhook URL

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Services to check
SERVICES=(
    "shopfloor-copilot:8010:/health"
    "opc-studio:8040:/health"
    "shopfloor-postgres:5432"
    "shopfloor-chroma:8000:/api/v1/heartbeat"
)

FAILED_SERVICES=()
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

echo "🏥 Health Check - ${timestamp}"
echo "=================================="

# Check Docker daemon
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon not running!${NC}"
    FAILED_SERVICES+=("Docker daemon")
fi

# Check each service
for service_info in "${SERVICES[@]}"; do
    IFS=':' read -r container port endpoint <<< "$service_info"
    
    # Check if container is running
    if ! docker ps | grep -q "$container"; then
        echo -e "${RED}❌ ${container} - Container not running${NC}"
        FAILED_SERVICES+=("${container}")
        continue
    fi
    
    # Check HTTP endpoint if provided
    if [ -n "$endpoint" ]; then
        if curl -sf "http://localhost:${port}${endpoint}" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ ${container} - Healthy${NC}"
        else
            echo -e "${RED}❌ ${container} - HTTP check failed${NC}"
            FAILED_SERVICES+=("${container}")
        fi
    else
        # Just check if container is running
        echo -e "${GREEN}✓ ${container} - Running${NC}"
    fi
done

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo -e "${RED}❌ Disk usage critical: ${DISK_USAGE}%${NC}"
    FAILED_SERVICES+=("Disk space")
else
    echo -e "${GREEN}✓ Disk usage: ${DISK_USAGE}%${NC}"
fi

# Check memory
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
if [ "$MEM_USAGE" -gt 90 ]; then
    echo -e "${RED}❌ Memory usage critical: ${MEM_USAGE}%${NC}"
    FAILED_SERVICES+=("Memory")
else
    echo -e "${GREEN}✓ Memory usage: ${MEM_USAGE}%${NC}"
fi

echo "=================================="

# Send alerts if there are failures
if [ ${#FAILED_SERVICES[@]} -gt 0 ]; then
    echo -e "${RED}Health check FAILED${NC}"
    
    # Create alert message
    ALERT_MSG="Shopfloor Copilot Health Check FAILED at ${timestamp}\n\nFailed services:\n"
    for service in "${FAILED_SERVICES[@]}"; do
        ALERT_MSG="${ALERT_MSG}- ${service}\n"
    done
    
    # Send email alert
    if command -v mail &> /dev/null && [ -n "$ALERT_EMAIL" ]; then
        echo -e "$ALERT_MSG" | mail -s "⚠️ Shopfloor Health Check Failed" "$ALERT_EMAIL"
        echo "📧 Alert email sent to ${ALERT_EMAIL}"
    fi
    
    # Send Slack alert
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"${ALERT_MSG}\"}" \
            > /dev/null 2>&1
        echo "📱 Alert sent to Slack"
    fi
    
    exit 1
else
    echo -e "${GREEN}All services healthy ✅${NC}"
    exit 0
fi
