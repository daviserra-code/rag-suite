# Phase 2 Setup Guide - KPI Dashboard

## What's New in Phase 2

✅ **SQL KPI Tool** - Read-only queries for MES production data
✅ **Mock MES Database** - PostgreSQL schemas with 14 days of A01 line data
✅ **KPI Dashboard Screen** - Interactive charts for OEE, FPY, MTTR
✅ **KPI API Endpoints** - RESTful access to production metrics

## Quick Start

### 1. Initialize MES Database

```bash
# From project root
python -m packages.tools.init_mes_db
```

This will create:
- `kpi_oee` - OEE metrics table (45 records)
- `kpi_fpy` - First Pass Yield table (45 records)
- `kpi_mttr` - Mean Time To Repair table (45 records)
- `downtime_events` - Downtime events table (9 records)

### 2. Verify Database

```bash
# Test KPI health endpoint
curl http://localhost:8010/api/health/kpi
```

### 3. Access KPI Dashboard

1. Start the application: `docker compose up`
2. Open: http://localhost:8010
3. Click **"KPI Dashboard"** tab
4. Select Line: **A01**
5. View metrics and trends

## API Endpoints

All KPI endpoints support optional filters:

### Get OEE Metrics
```bash
GET /api/kpi/oee?line=A01&start_date=2025-11-15&end_date=2025-11-23
```

### Get FPY Metrics
```bash
GET /api/kpi/fpy?line=A01
```

### Get MTTR Metrics
```bash
GET /api/kpi/mttr?line=A01
```

### Get Downtime Events
```bash
GET /api/kpi/downtime?line=A01&limit=10
```

### Get Line Summary
```bash
GET /api/kpi/summary/A01?days=7
```

## Sample Data

### Line A01 - 7 Day Averages
- **OEE**: 77.8%
- **FPY**: 96.4%
- **MTTR**: 16.8 minutes

### Recent Performance (Last 3 Shifts)
| Shift | OEE | FPY | Downtime |
|-------|-----|-----|----------|
| T1    | 76.4% | 96.8% | 70 min |
| T2    | 75.3% | 95.2% | 57 min |
| T3    | 72.9% | 97.1% | 86 min |

## Features

### KPI Dashboard Screen
- **Real-time Metrics**: OEE, FPY, MTTR cards
- **Trend Charts**: 7/14/30 day historical view using Plotly
- **Downtime Log**: Recent failure events with reasons
- **Line Selector**: Switch between A01, A02, B01
- **Time Range**: 7/14/30 day filters

### SQL KPI Tool
- **Whitelisted Queries**: Safe read-only access
- **Connection Pooling**: Efficient database access
- **Error Handling**: Graceful fallbacks
- **Parameterized Queries**: SQL injection protection

## Troubleshooting

### Database Not Initialized
```
Error: relation "kpi_oee" does not exist
```
**Solution**: Run `python -m packages.tools.init_mes_db`

### No KPI Data Showing
1. Check database health: `curl http://localhost:8010/api/health/kpi`
2. Verify PostgreSQL is running: `docker ps | grep postgres`
3. Check connection settings in `.env`:
   ```
   POSTGRES_HOST=postgres
   POSTGRES_PORT=5432
   POSTGRES_DB=ragdb
   ```

### Charts Not Loading
- Ensure Plotly is installed: `pip install plotly==5.24.1`
- Check browser console for JavaScript errors
- Verify data is returned from API endpoints

## Next Steps

### Phase 3 Features (Coming Soon)
- **Real MES Connector**: Connect to Siemens Opcenter Execution
- **KPI Chat Interface**: Ask "What caused the OEE drop?" with Ollama
- **Predictive Alerts**: AI-powered anomaly detection
- **Drill-down Analysis**: Click metrics to see detailed breakdowns
- **Export Reports**: PDF generation for shift/weekly reports

## File Structure

```
packages/tools/
├── __init__.py
├── sqlkpi.py              # KPI query functions
└── init_mes_db.py         # Database initialization

apps/shopfloor_copilot/
├── routers/
│   └── kpi.py             # KPI API endpoints
└── screens/
    └── kpi_dashboard_interactive.py  # Dashboard UI
```

## Sample Queries

### Get Today's OEE
```python
from packages.tools.sqlkpi import get_oee_metrics
from datetime import date

metrics = get_oee_metrics(
    line="A01",
    start_date=str(date.today()),
    end_date=str(date.today())
)
```

### Get Weekly Summary
```python
from packages.tools.sqlkpi import get_line_summary

summary = get_line_summary("A01", days=7)
print(f"Average OEE: {summary['avg_oee']}%")
print(f"Average FPY: {summary['avg_fpy']}%")
print(f"Average MTTR: {summary['avg_mttr_minutes']} minutes")
```

## Configuration

All settings in `.env`:
```bash
# KPI Database (Read-Only Replica)
SQL_KPI_ENABLED=true
POSTGRES_REPLICA_HOST=postgres
POSTGRES_REPLICA_PORT=5432
POSTGRES_REPLICA_DB=ragdb
POSTGRES_REPLICA_USER=postgres
POSTGRES_REPLICA_PASSWORD=postgres
```

For production, use a **read-only replica** to avoid impacting the operational MES database.
