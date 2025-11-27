# RAG Suite - Shopfloor Copilot

**AI-powered Manufacturing Operations Platform with Real-time Monitoring, RAG Q&A, and Automated Reporting**

## 🚀 Quick Start

```bash
cp .env.example .env
docker compose up --build
```

**Access:**
- UI: http://localhost:8000/app
- API: http://localhost:8000/docs

## ✨ Features

### 📊 Core Capabilities
- **Production Lines Monitoring** - Real-time OEE tracking across 6 production lines
- **Plant Overview** - Interactive facility visualization with line status
- **Operations Dashboard** - Comprehensive analytics and downtime analysis
- **KPI Dashboard** - Performance metrics with trend analysis
- **Ticket Insights** - Jira integration for issue tracking (with demo mode)
- **Automated Reporting** - Scheduled daily/weekly/monthly PDF reports
- **Q&A System** - RAG-powered technical documentation Q&A
- **Export Capabilities** - CSV and PDF export for all dashboards

### 🎯 Key Technologies
- **NiceGUI** - Modern Python UI framework
- **ChromaDB** - Vector database for RAG
- **PostgreSQL** - Time-series OEE data storage
- **Docker** - Containerized deployment
- **Jira MCP** - Optional ticket integration

## 📈 Reporting System

### Generate Reports

**Via UI:**
1. Navigate to **Reports** tab
2. Select report type (Daily, Weekly, Monthly, Quarterly, Annual)
3. Or use Quick Actions (Yesterday, Last 7/30/90 Days)
4. Click "Generate Report"

**Via Command Line:**
```bash
# Weekly report
docker exec -i rag-suite-api-1 python /app/generate_report.py --type weekly --output /tmp/report.pdf

# Custom 60-day report
docker exec -i rag-suite-api-1 python /app/generate_report.py --days 60 --output /tmp/report.pdf
```

### Scheduled Reports

Configure automated reports in `.env`:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@company.com
SMTP_PASSWORD=your-app-password
REPORT_EMAILS=manager@company.com,director@company.com
```

**Default Schedule:**
- Daily: 06:00 every day
- Weekly: 08:00 every Monday
- Monthly: 09:00 on 1st of month

**Start scheduler:**
```bash
docker exec -d rag-suite-api-1 python /app/report_scheduler.py
```

### Report Contents
- Executive Summary with Key Metrics
- Production Line Performance Analysis
- Downtime Analysis by Category
- Top 10 Issues and Root Causes
- Shift Performance Comparison

📖 **[Full Reporting Documentation](docs/REPORTING.md)**

## 🏭 Plant Simulation

Generate realistic historical OEE data for demonstrations:

```bash
# Generate 90 days of data
docker exec -i rag-suite-api-1 python /app/simulate_plant_history.py 90

# Generate 180 days
docker exec -i rag-suite-api-1 python /app/simulate_plant_history.py 180
```

**Simulation Features:**
- 6 production lines with unique characteristics
- Realistic shift variations (Night -2-6%, Morning +0-5%)
- Day-of-week effects (Monday ramp-up, Friday fatigue)
- 10 downtime types with realistic durations
- Random variations simulating real-world unpredictability

## 🎫 Jira Integration

**Demo Mode (Default):**
- Works without Jira instance
- 12 sample issues with realistic data
- 4 AI-identified patterns

**Real Jira Integration:**
1. Add to `.env`:
```env
ATLASSIAN_HOST=your-company.atlassian.net
ATLASSIAN_EMAIL=your-email@company.com
ATLASSIAN_TOKEN=your-api-token
JIRA_MCP_URL=http://jira-mcp:3000/mcp
```
2. Restart: `docker-compose restart api`
3. Toggle "Demo Mode" off in Ticket Insights tab

📖 **[Jira Integration Guide](docs/JIRA_INTEGRATION.md)**

## 📚 Documentation

- **[Reporting System](docs/REPORTING.md)** - Automated report generation and scheduling
- **[Jira Integration](docs/JIRA_INTEGRATION.md)** - Ticket tracking setup and API

## 🔧 Architecture

```
rag-suite/
├── apps/
│   ├── shopfloor_copilot/    # Main UI application
│   │   ├── screens/           # Individual dashboard screens
│   │   ├── main.py           # Entry point
│   │   └── ui.py             # Tab navigation
│   └── core_api/             # RAG API endpoints
├── packages/
│   ├── core_rag/             # ChromaDB, embeddings, retrieval
│   ├── core_ingest/          # Document ingestion pipeline
│   ├── jira_integration/     # Jira MCP client
│   └── export_utils/         # PDF/CSV export
├── data/
│   ├── migrations/           # Database schemas
│   └── reports/              # Generated report archive
├── generate_report.py        # Report generation script
├── report_scheduler.py       # Automated report scheduler
└── simulate_plant_history.py # Plant data simulator
```

## 🎨 Dashboards

### 1. Production Lines
- Real-time status (🟢 Running, 🟡 Warning, 🔴 Stopped)
- OEE trends over 7/30/90 days
- Per-line drill-down analysis
- Historical performance comparison

### 2. Plant Overview
- Interactive facility layout
- Line status visualization
- Click-through to Operations Dashboard

### 3. Operations Dashboard
- Shift-by-shift OEE breakdown
- Downtime analysis by category
- 6-loss Pareto analysis
- Export to CSV/PDF

### 4. KPI Dashboard
- Current shift metrics
- 24-hour trends
- Performance vs targets
- Quality metrics

### 5. Ticket Insights
- Active sprint overview
- Issue status distribution
- AI pattern detection
- Blocker alerts

### 6. Reports
- On-demand report generation
- Scheduled report management
- Report history and downloads
- Email configuration

### 7. Q&A System
- RAG-powered technical Q&A
- AI-generated filter checklists
- Answer citations with sources
- Document reference links

## 🚀 Production Deployment

### Environment Variables

Required:
```env
DATABASE_URL=postgresql://user:pass@postgres:5432/ragdb
CHROMA_HOST=chroma
CHROMA_PORT=8000
```

Optional:
```env
# Jira Integration
ATLASSIAN_HOST=your-company.atlassian.net
ATLASSIAN_EMAIL=your-email@company.com
ATLASSIAN_TOKEN=your-api-token

# Email Reports
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@company.com
SMTP_PASSWORD=your-app-password
REPORT_EMAILS=manager@company.com,director@company.com
```

### Docker Compose Services
- `api` - Main application (NiceGUI)
- `postgres` - Time-series database
- `chroma` - Vector database
- `jira-mcp` - Jira integration (optional)

## 📊 Data Model

### OEE Tables
- `oee_line_shift` - Shift-level performance metrics
- `oee_downtime_events` - Downtime event log
- `report_history` - Generated report tracking

### RAG Collections
- `shopfloor_docs` - Technical documentation chunks

## 🛠 Development

### Adding New Dashboards

1. Create screen file in `apps/shopfloor_copilot/screens/`
2. Import in `ui.py`
3. Add tab to `build_ui()`
4. Implement `render_*()` function

### Custom Report Templates

Modify `generate_report.py` to add custom sections:

```python
def generate_custom_report(start_date, end_date):
    # Add your custom data queries
    custom_data = get_custom_data()
    
    # Build custom HTML
    html = f"<h2>Custom Section</h2>..."
    
    # Generate PDF
    return export_to_pdf(title="Custom Report", content_html=html)
```

## 📈 Performance

- **Report Generation:** 7 days <100ms, 90 days <500ms, 365 days <2s
- **Dashboard Load:** <200ms with caching
- **RAG Query:** <1s with reranking
- **Export:** <2s for full dataset

## 🎯 Siemens Presentation Ready

This platform is configured for demonstration with:
- ✅ 90 days of realistic historical data
- ✅ All dashboards populated with trends
- ✅ Mock Jira data for ticket insights
- ✅ Professional PDF reports ready to generate
- ✅ Real-time status indicators
- ✅ Comprehensive export capabilities

**Quick Demo Flow:**
1. **Production Lines** - Show real-time monitoring
2. **Operations** - Dive into downtime analysis
3. **KPI Dashboard** - Highlight performance trends
4. **Reports** - Generate executive summary
5. **Ticket Insights** - Show issue tracking integration

---

**Version:** 2.0.0  
**Last Updated:** November 27, 2025  
**Built for:** Siemens Manufacturing Demo
