# Chapter 1: Introduction & Overview

**Version:** 0.3.1  
**Last Updated:** December 26, 2025  
**Status:** Production Ready ✅

---

## What's New in v0.3.1

### Recent Improvements (December 22-26, 2025)

Shopfloor Copilot has received **major UI/UX enhancements** and **bug fixes** based on user feedback:

- ✅ **21 Issues Fixed:** Functional bugs, readability issues, and accessibility improvements
- ✅ **15 Screens Enhanced:** Complete redesign of Operator Q&A, plus improvements across all dashboards
- ✅ **WCAG AA Compliant:** All text now meets accessibility standards for contrast (4.5:1 ratio)
- ✅ **Modern UI:** Gradient cards, bold typography, Material Design patterns
- ✅ **Better UX:** Clear error messages, helpful tooltips, improved feedback

**Key Highlights:**
- **AI Diagnostics:** Now accepts flexible station IDs (e.g., "20", "st20", "ST20")
- **Operator Q&A:** Complete redesign with modern chat interface
- **All Dashboards:** Improved text contrast, larger fonts, clearer layouts
- **OPC Explorer:** Better connection error handling with troubleshooting tips
- **Shift Handover:** Readable filters and report text

For detailed changes, see [CHANGELOG.md](CHANGELOG.md).

[📸 SCREENSHOT PLACEHOLDER]
**File:** `screenshots/dashboard-overview-v031.png`
**Caption:** Shopfloor Copilot v0.3.1 dashboard showing new UI improvements
**Instructions:**
1. Navigate to main dashboard (Home tab)
2. Capture full screen showing modern UI with gradient cards
3. Include visible text demonstrating improved contrast

---

## What is Shopfloor Copilot?

**Shopfloor Copilot** is an AI-powered Manufacturing Execution System (MES) companion that transforms traditional manufacturing monitoring into intelligent decision support.

### The Vision

Traditional MES systems tell you **WHAT** is happening:
> "Line A01 is down."

Shopfloor Copilot tells you **WHAT, WHY, and HOW TO FIX**:
> "Line A01 is down because station ST17 is FAULTED (availability.equipment_failure). This typically requires sensor reset and belt inspection per WI-23."

### Key Capabilities

1. **Real-Time Monitoring** (Sprint 1)
   - Connect to OPC UA servers
   - Browse equipment hierarchy
   - Monitor live values
   - Track value changes

2. **Semantic Understanding** (Sprint 2)
   - Transform raw tags into meaningful signals
   - Automatic loss category classification
   - OEE KPI calculation
   - Standardized naming across vendors

3. **AI Diagnostics** (Sprint 3)
   - Explainable root cause analysis
   - Evidence-based recommendations
   - RAG-grounded procedures
   - Structured 4-section output

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Shopfloor Copilot UI                        │
│              (23 Tabs - NiceGUI Interface)                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼──────┐  ┌──▼──────┐  ┌──▼──────────┐
│   OPC    │  │  Core   │  │ Diagnostics │
│  Studio  │  │   API   │  │   Engine    │
└───┬──────┘  └──┬──────┘  └──┬──────────┘
    │            │            │
┌───▼──────┐  ┌─▼────┐  ┌───▼────┐
│ OPC Demo │  │Chroma│  │ Ollama │
│  Server  │  │  DB  │  │  LLM   │
└──────────┘  └──────┘  └────────┘
```

### Component Overview

| Component | Purpose | Port | Technology |
|-----------|---------|------|------------|
| **Shopfloor Copilot** | Main UI & Diagnostics API | 8010 | NiceGUI, FastAPI |
| **OPC Studio** | OPC UA client + Semantic engine | 8040 | FastAPI, asyncua |
| **OPC Demo Server** | Simulated plant (24 stations) | 4850 | asyncua |
| **Core API** | RAG/LLM backend | 8000 | FastAPI |
| **ChromaDB** | Vector database (knowledge) | 8001 | ChromaDB |
| **Ollama** | LLM inference | 11434 | llama3.2 |
| **PostgreSQL** | MES data storage | 5432 | PostgreSQL 16 |

---

## Key Features

### 🔍 OPC Explorer (Sprint 1)
- **UAExpert-like** OPC UA client
- Hierarchical node browser
- Live value monitoring
- Read/write operations
- Watchlist with auto-refresh
- Connection management

### 🗺️ Semantic Mapping (Sprint 2)
- **Kepware-like** tag mapping
- YAML-driven configuration
- 19 loss categories (availability, performance, quality, non-productive)
- Automatic OEE classification
- 7 derived KPIs
- 4 station types supported

### 🤖 AI Diagnostics (Sprint 3)
- **Explainable** root cause analysis
- Grounded in runtime evidence
- RAG-powered recommendations
- 4-section structured output
- No hallucination (strict guardrails)
- LLM-powered reasoning

---

## Use Cases

### For Production Operators
**Problem:** "My station is showing an alarm. What should I do?"

**Solution:**
1. Navigate to OPC Explorer → See real-time status
2. Go to Semantic Signals → See `loss_category` classification
3. Open AI Diagnostics → Get step-by-step troubleshooting guide

### For Line Managers
**Problem:** "Why is Line A01 underperforming today?"

**Solution:**
1. Check KPI Dashboard → See availability drop
2. View Semantic Signals → Identify `performance.reduced_speed` on multiple stations
3. Request AI Diagnostic for line → Get correlated root cause analysis

### For Maintenance Engineers
**Problem:** "Which stations need preventive maintenance?"

**Solution:**
1. Review Station Heatmap → Identify high-failure stations
2. Check Semantic Signals → See recurring `availability.equipment_failure`
3. AI Diagnostics → Get maintenance checklist with procedure references

### For Plant Managers
**Problem:** "What are our biggest OEE losses this month?"

**Solution:**
1. Comparative Analytics → See loss category trends
2. Reports Dashboard → Generate loss pareto chart
3. AI Diagnostics for top losers → Get improvement recommendations

---

## Technology Stack

### Backend
- **Language:** Python 3.11
- **Web Framework:** FastAPI 0.115.2
- **OPC UA:** asyncua 1.1.5
- **Database:** PostgreSQL 16
- **Vector DB:** ChromaDB 0.5.20
- **LLM:** Ollama (llama3.2)

### Frontend
- **UI Framework:** NiceGUI 2.9.3
- **Styling:** Tailwind CSS
- **Charts:** Plotly, Matplotlib

### Infrastructure
- **Containerization:** Docker 24.0+
- **Orchestration:** Docker Compose 2.20+
- **Reverse Proxy:** Built-in FastAPI

---

## Security & Compliance

### Access Control
- Session-based authentication (NiceGUI storage)
- Role-based access control (RBAC) ready
- Operator vs Manager views

### Data Protection
- No PII stored in AI diagnostics
- RAG retrieval filtered by metadata
- Audit logs for all diagnostics

### Industrial Standards
- **OPC UA:** IEC 62541 compliant
- **OEE:** ISO 22400 compatible
- **Loss Categories:** ANSI/ISA-95 aligned

---

## Limitations & Constraints

### Current Limitations
1. **Station Types:** Only 4/12 types have semantic mappings
2. **RAG Content:** Limited work instructions in demo
3. **Historical Analysis:** Real-time only (no time-series DB yet)
4. **LLM Speed:** 10-30 seconds for diagnostic generation
5. **Language:** English only (Italian planned)

### Design Constraints
1. **Read-Only:** AI never controls equipment (safety)
2. **Human-in-the-Loop:** All actions require operator confirmation
3. **Evidence-Based:** AI cannot invent data or causes
4. **Structured Output:** Always 4 sections (no free-form)

---

## Performance Metrics

### Response Times
- **OPC Read:** < 100ms
- **Snapshot Generation:** < 200ms
- **Semantic Transformation:** < 50ms per station
- **RAG Retrieval:** < 1 second
- **AI Diagnostic:** 10-30 seconds (LLM inference)

### Scalability
- **Stations Monitored:** 24 (demo), 100+ (production)
- **Concurrent Users:** 10+ operators
- **OPC Update Rate:** 1 Hz (1 second)
- **Watchlist Size:** Unlimited nodes

### Reliability
- **Uptime Target:** 99.5%
- **Connection Recovery:** Automatic reconnect
- **Graceful Degradation:** Works without RAG/LLM
- **Error Handling:** No crashes on bad data

---

## System Requirements

### Server Requirements
- **CPU:** 4 cores minimum (8 recommended)
- **RAM:** 8 GB minimum (16 GB recommended)
- **Storage:** 50 GB minimum (100 GB recommended)
- **Network:** 1 Gbps LAN

### Client Requirements
- **Browser:** Chrome 90+, Firefox 88+, Edge 90+
- **Screen:** 1920x1080 minimum
- **Network:** 10 Mbps minimum

### Docker Requirements
- **Docker:** 24.0+
- **Docker Compose:** 2.20+
- **OS:** Linux (Ubuntu 20.04+), Windows 10+ (WSL2), macOS 11+

---

## Getting Help

### Documentation
- **This Guide:** Complete feature documentation
- **API Docs:** http://localhost:8010/docs
- **Sprint Summary:** [SPRINT_SUMMARY.md](../../SPRINT_SUMMARY.md)

### Community
- **GitHub:** [Issues](https://github.com/your-org/rag-suite/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/rag-suite/discussions)

### Support
- **Email:** support@your-company.com
- **Hours:** Mon-Fri 9am-5pm CET

---

**Next Chapter:** [Installation & Setup →](02-installation.md)
