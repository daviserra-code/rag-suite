# Reporting System Documentation

## Overview

The Shopfloor Copilot reporting system provides automated and on-demand generation of comprehensive plant operations reports. Reports can be generated manually through the UI or scheduled for automatic delivery via email.

## Features

### 📊 Report Types

1. **Daily Report** - Last 24 hours
2. **Weekly Report** - Last 7 days
3. **Monthly Report** - Last 30 days
4. **Quarterly Report** - Last 90 days
5. **Annual Report** - Last 365 days
6. **Custom Report** - Any number of days

### 📈 Report Contents

Each report includes:

#### Executive Summary
- **Key Metrics Cards**
  - Average OEE (Overall Equipment Effectiveness)
  - Total Units Produced
  - Scrap Rate
  - Average Unplanned Downtime

- **OEE Components Breakdown**
  - Availability %
  - Performance %
  - Quality %
  - Visual progress bars

#### Production Line Performance
- Per-line OEE, Availability, Performance, Quality
- Units produced and good units
- Scrap percentage
- Color-coded performance indicators
  - 🟢 Green: OEE ≥ 75%
  - 🟡 Yellow: OEE 65-74%
  - 🔴 Red: OEE < 65%

#### Downtime Analysis
- Breakdown by loss category
- Event counts per category
- Total duration (hours)
- Average duration per event (minutes)

#### Top 10 Downtime Issues
- Ranked by total impact duration
- Line identification
- Issue description and category
- Number of occurrences
- Total time lost

#### Shift Performance Comparison
- Morning, Afternoon, Night shift metrics
- OEE and component breakdown per shift
- Units produced per shift
- Identifies best and worst performing shifts

### 🎯 Generation Methods

#### 1. Manual Generation (UI)

Access the **Reports** tab in the Shopfloor Copilot UI:

1. Select report type (daily, weekly, monthly, etc.)
2. Or use Quick Actions buttons (Yesterday, Last 7/30/90 Days)
3. For custom reports, select "custom" and specify days
4. Click "🎯 Generate Report"
5. Report automatically downloads as PDF

#### 2. Command Line

Generate reports directly from the command line:

```bash
# Weekly report
docker exec -i rag-suite-api-1 python /app/generate_report.py --type weekly --output /tmp/report.pdf

# Monthly report
docker exec -i rag-suite-api-1 python /app/generate_report.py --type monthly --output /tmp/report.pdf

# Custom 60-day report
docker exec -i rag-suite-api-1 python /app/generate_report.py --days 60 --output /tmp/report.pdf
```

#### 3. Scheduled Reports

Automated reports run on schedule and email to configured recipients.

**Default Schedule:**
- **Daily**: 06:00 every day
- **Weekly**: 08:00 every Monday
- **Monthly**: 09:00 on 1st of month

## Configuration

### Email Setup

Configure email delivery in your `.env` file:

```env
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@company.com
SMTP_PASSWORD=your-app-password

# Report Recipients (comma-separated)
REPORT_EMAILS=manager@company.com,director@company.com,ops@company.com

# Optional: Run test report on scheduler start
RUN_REPORT_ON_START=false
```

**For Gmail:**
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the App Password as `SMTP_PASSWORD`

### Running the Scheduler

Start the report scheduler as a background service:

```bash
# Run scheduler in background
docker exec -d rag-suite-api-1 python /app/report_scheduler.py

# View scheduler logs
docker logs -f rag-suite-api-1 | grep "REPORT"
```

### Archive Storage

All generated reports are automatically saved to:
```
/app/data/reports/
```

File naming format: `{type}_{YYYYMMDD_HHMMSS}.pdf`

Example: `weekly_20251127_060000.pdf`

## Report History

Report generation history is tracked in the database:

```sql
-- View recent reports
SELECT 
    report_type,
    period_start,
    period_end,
    generated_at,
    file_size_kb,
    recipients_count
FROM report_history
ORDER BY generated_at DESC
LIMIT 20;
```

## Integration with Other Systems

### API Integration

The reporting system can be integrated with external systems:

```python
from generate_report import generate_executive_report
from datetime import datetime, timedelta

# Generate report for last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

pdf_bytes = generate_executive_report(start_date, end_date, "monthly")

# Save or send the PDF
with open("report.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### Webhook Integration

Configure webhooks to trigger report generation:

```python
# Example: Generate report on demand
@app.post("/api/generate-report")
async def trigger_report(report_type: str):
    days_map = {"daily": 1, "weekly": 7, "monthly": 30}
    days = days_map.get(report_type, 7)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    pdf_bytes = generate_executive_report(start_date, end_date, report_type)
    
    return Response(content=pdf_bytes, media_type="application/pdf")
```

## Best Practices

### For Operators
1. **Generate daily reports** at shift handover to review previous shift performance
2. **Use quick action buttons** for common time periods
3. **Download reports** before important meetings for offline access

### For Managers
1. **Review weekly reports** every Monday to identify trends
2. **Compare monthly reports** to track improvement initiatives
3. **Share quarterly reports** with stakeholders during business reviews

### For Maintenance
1. **Analyze downtime reports** to prioritize preventive maintenance
2. **Track top 10 issues** monthly to measure improvement efforts
3. **Compare shift performance** to identify training needs

## Troubleshooting

### Reports Not Generating

**Check database connection:**
```bash
docker exec -i rag-suite-api-1 psql $DATABASE_URL -c "SELECT COUNT(*) FROM oee_line_shift;"
```

**Verify data exists for period:**
```sql
SELECT date, COUNT(*) 
FROM oee_line_shift 
GROUP BY date 
ORDER BY date DESC 
LIMIT 10;
```

### Email Not Sending

1. **Verify SMTP credentials** in `.env`
2. **Check firewall** allows outbound SMTP
3. **Test connection** manually:
```bash
docker exec -i rag-suite-api-1 python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@company.com', 'your-password')
print('✅ Connection successful')
"
```

### Report Archive Full

Clean up old reports:
```bash
# Remove reports older than 90 days
docker exec -i rag-suite-api-1 find /app/data/reports -name "*.pdf" -mtime +90 -delete

# Or keep only last 100 reports
docker exec -i rag-suite-api-1 bash -c "
cd /app/data/reports && 
ls -t | tail -n +101 | xargs rm -f
"
```

## Performance Optimization

### Large Date Ranges

For reports covering 180+ days:
- Report generation may take 10-30 seconds
- Consider caching frequently requested reports
- Use background task queue for UI requests

### Database Queries

Reports use optimized queries with:
- Indexed date columns
- Aggregation at database level
- Minimal data transfer

Average query times:
- 7 days: <100ms
- 30 days: <200ms
- 90 days: <500ms
- 365 days: <2s

## Future Enhancements

### Planned Features
- [ ] Report comparison (month-over-month, year-over-year)
- [ ] Custom report templates
- [ ] Excel export format
- [ ] Interactive drill-down reports
- [ ] Automated insights and recommendations
- [ ] Mobile-optimized report viewer
- [ ] Multi-language support
- [ ] Custom branding per recipient

### Integration Roadmap
- [ ] Power BI connector
- [ ] Slack notifications
- [ ] Teams integration
- [ ] SharePoint upload
- [ ] API for third-party BI tools

## Support

For questions or issues with the reporting system:

1. **Check logs:** `docker logs rag-suite-api-1`
2. **Review documentation:** This file and related docs
3. **Test manually:** Use command line generation to isolate issues
4. **Contact:** Production Management team

---

**Last Updated:** November 27, 2025  
**Version:** 1.0.0
