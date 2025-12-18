#!/bin/bash
# Setup cron jobs for automated maintenance
# Run once after deployment: ./scripts/setup-cron.sh

set -e

SCRIPT_DIR="/home/${USER}/shopfloor-deploy/scripts"
CRONTAB_FILE="/tmp/shopfloor-cron"

echo "⏰ Setting up cron jobs for Shopfloor Copilot"
echo "=============================================="

# Create cron entries
cat > "${CRONTAB_FILE}" << EOF
# Shopfloor Copilot Automated Maintenance
# Generated on $(date)

# Daily backup at 2 AM
0 2 * * * ${SCRIPT_DIR}/backup.sh >> /var/log/shopfloor-backup.log 2>&1

# Health check every 5 minutes
*/5 * * * * ${SCRIPT_DIR}/health-check.sh >> /var/log/shopfloor-health.log 2>&1

# Weekly Docker cleanup on Sunday at 3 AM
0 3 * * 0 docker system prune -af --volumes >> /var/log/shopfloor-cleanup.log 2>&1

# Rotate logs daily at 4 AM
0 4 * * * find /var/log -name "shopfloor-*.log" -type f -mtime +7 -delete

# SSL certificate renewal check (Let's Encrypt auto-renews, but check monthly)
0 5 1 * * sudo certbot renew --quiet

# Update Docker images weekly on Monday at 1 AM (review before enabling)
# 0 1 * * 1 cd /home/${USER}/rag-suite && docker compose pull && docker compose up -d

EOF

# Install cron jobs
crontab "${CRONTAB_FILE}"
rm "${CRONTAB_FILE}"

echo ""
echo "✅ Cron jobs installed successfully!"
echo ""
echo "Scheduled tasks:"
echo "  ✓ Daily backup at 2:00 AM"
echo "  ✓ Health checks every 5 minutes"
echo "  ✓ Weekly Docker cleanup on Sundays at 3:00 AM"
echo "  ✓ Log rotation daily at 4:00 AM"
echo "  ✓ SSL certificate renewal check on 1st of month"
echo ""
echo "View cron jobs: crontab -l"
echo "Edit cron jobs: crontab -e"
echo ""
echo "Log files:"
echo "  - /var/log/shopfloor-backup.log"
echo "  - /var/log/shopfloor-health.log"
echo "  - /var/log/shopfloor-cleanup.log"
echo ""
