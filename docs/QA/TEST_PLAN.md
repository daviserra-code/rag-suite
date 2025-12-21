# Shopfloor Copilot + OPC Studio — QA Test Plan

**Version:** 1.0  
**Last Updated:** December 21, 2025  
**Status:** Production-Ready

---

## Overview

This test plan provides a layered validation approach for the Shopfloor Copilot system, covering:
- Runtime health and service availability
- OPC UA connectivity and data acquisition (Sprint 1)
- Semantic mapping engine (Sprint 2)
- Phase B unified runtime views with fallback logic
- Sprint 3 diagnostics with AI explainability
- Regression testing for production safety

**Test Environment Configuration:**
- `SHOPFLOOR_API_URL`: http://localhost:8010 (default)
- `SHOPFLOOR_UI_URL`: http://localhost:8010 (default)
- `OPC_STUDIO_URL`: http://localhost:8040 (default)
- `POSTGRES_HOST`: localhost
- `POSTGRES_PORT`: 5432
- `POSTGRES_DB`: ragdb
- `POSTGRES_USER`: postgres
- `POSTGRES_PASSWORD`: postgres (or from .env)

---

## Layer 0 — Runtime & Service Health

### Objective
Verify all Docker containers are running and healthy.

### Test Steps

#### 1. Check Container Status
```bash
docker compose ps
```

**Expected Result:**
- All services show `Up` or `Up (healthy)` status
- No services in `Restarting` or `Exited` state

**Services to verify:**
- `shopfloor-copilot` (UI + API)
- `opc-studio` (OPC UA bridge)
- `shopfloor-postgres` (database)
- `shopfloor-chroma` (vector store)
- `shopfloor-ollama` (LLM)
- `shopfloor-data-sim` (continuous data generator)

#### 2. Check Service Health Endpoints

**OPC Studio Health:**
```bash
curl http://localhost:8040/health
```
**Expected:** `{"status":"ok"}`

**Shopfloor API Health:**
```bash
curl http://localhost:8010/health
```
**Expected:** `{"status":"ok","app":"shopfloor_copilot"}`

**Shopfloor UI:**
```bash
curl -I http://localhost:8010/
```
**Expected:** `HTTP/1.1 200 OK`

#### 3. Check Logs for Errors

**View OPC Studio logs:**
```bash
docker compose logs -f opc-studio
```

**View API logs:**
```bash
docker compose logs -f shopfloor-copilot
```

**View UI logs:**
```bash
docker compose logs -f shopfloor-copilot
```

**Expected:**
- No Python stack traces
- No connection errors
- No crash loops

---

## Layer 1 — OPC Explorer (Sprint 1)

### Objective
Validate OPC UA client functionality: connect, browse, read, subscribe.

### Test Steps

#### 1. Connect to OPC UA Server

**Request:**
```bash
curl -X POST http://localhost:8040/opc/connect \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "opc.tcp://localhost:4840"
  }'
```

**Expected:**
```json
{
  "status": "connected",
  "endpoint": "opc.tcp://localhost:4840"
}
```

#### 2. Browse Root Node

**Request:**
```bash
curl "http://localhost:8040/opc/browse?nodeId=ns=0;i=85"
```

**Expected:**
- Returns JSON array of child nodes
- Each node has: `nodeId`, `displayName`, `nodeClass`, `hasChildren`
- No empty array (root should have children)

**Example:**
```json
{
  "children": [
    {
      "nodeId": "ns=0;i=86",
      "displayName": "Objects",
      "nodeClass": "Object",
      "hasChildren": true
    }
  ]
}
```

#### 3. Read Multiple Nodes

**Request:**
```bash
curl -X POST http://localhost:8040/opc/read \
  -H "Content-Type: application/json" \
  -d '{
    "nodeIds": [
      "ns=2;s=Demo.Dynamic.Scalar.Float",
      "ns=2;s=Demo.Static.Scalar.Int32"
    ]
  }'
```

**Expected:**
- Returns array of values
- Each value has: `nodeId`, `value`, `timestamp`, `statusCode`
- `statusCode` = "Good"

#### 4. Subscribe to Watchlist

**Add nodes to watchlist:**
```bash
curl -X POST http://localhost:8040/opc/watchlist \
  -H "Content-Type: application/json" \
  -d '{
    "nodeIds": [
      "ns=2;s=Demo.Dynamic.Scalar.Float",
      "ns=2;s=A01.OEE"
    ]
  }'
```

**Get watchlist updates:**
```bash
curl http://localhost:8040/opc/watchlist
```

**Expected:**
- Returns current values for subscribed nodes
- Timestamps update on subsequent calls (values are live)
- No stale data (timestamps within last 5 seconds)

---

## Layer 2 — Semantic Mapping (Sprint 2)

### Objective
Verify semantic mapping engine loads YAML configurations and generates enriched snapshots.

### Test Steps

#### 1. Load Valid Mapping

**Request:**
```bash
curl -X POST http://localhost:8040/mapping/load \
  -H "Content-Type: application/json" \
  -d '{
    "yaml_path": "config/plant_mapping.yaml"
  }'
```

**Expected:**
```json
{
  "status": "success",
  "message": "Mapping loaded successfully",
  "lines_mapped": 1,
  "stations_mapped": 5
}
```

#### 2. Load Invalid Mapping (Negative Test)

**Request:**
```bash
curl -X POST http://localhost:8040/mapping/load \
  -H "Content-Type: application/json" \
  -d '{
    "yaml_path": "config/invalid_mapping.yaml"
  }'
```

**Expected:**
- HTTP 400 or 422
- Error message describes schema violation
- No application crash

#### 3. Fetch Semantic Snapshot

**Request:**
```bash
curl http://localhost:8040/semantic/snapshot
```

**Expected Structure:**
```json
{
  "plant": {
    "id": "FAB01",
    "name": "Main Assembly Plant"
  },
  "lines": [
    {
      "id": "A01",
      "name": "Assembly Line A01",
      "stations": [
        {
          "id": "ST17",
          "name": "Welding Station",
          "signals": [
            {
              "name": "cycle_time",
              "nodeId": "ns=2;s=A01.ST17.CycleTime",
              "unit": "seconds",
              "loss_category": "performance"
            }
          ]
        }
      ],
      "kpis": {
        "availability": 0.95,
        "performance": 0.87,
        "quality": 0.98,
        "oee": 0.81
      }
    }
  ]
}
```

**Validation Criteria:**
- `loss_category` present on signals (performance, availability, quality)
- KPIs calculated: availability, performance, quality, oee
- All mapped stations include signal lists
- No null nodeIds or missing units

---

## Layer 3 — Phase B Unified Runtime Views

### Objective
Verify unified runtime views with OPC + simulation fallback logic.

### Test Steps

#### 1. Verify Database Views Exist

**Connect to database:**
```bash
psql -h localhost -p 5432 -U postgres -d ragdb
```

**Check views:**
```sql
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public' 
  AND table_name LIKE 'v_runtime%';
```

**Expected:**
- `v_runtime_kpi`
- `v_runtime_events`
- `v_runtime_line_status`

#### 2. Query Runtime KPIs (OPC Live)

**Ensure OPC Studio is running:**
```bash
docker compose ps opc-studio
```

**Query:**
```sql
SELECT * FROM v_runtime_kpi 
WHERE line_id = 'A01' 
ORDER BY ts DESC 
LIMIT 5;
```

**Expected:**
- Records exist with recent timestamps (within last 5 minutes)
- `source` column = 'opc' (when OPC is live and mapped)
- `availability`, `performance`, `quality`, `oee` values between 0 and 1

#### 3. Test Fallback to Simulation

**Stop OPC Studio:**
```bash
docker compose stop opc-studio
```

**Wait for staleness window (configurable, default 5 minutes):**
```bash
sleep 60  # Wait 1 minute for testing
```

**Query again:**
```sql
SELECT * FROM v_runtime_line_status 
ORDER BY last_ts DESC 
LIMIT 10;
```

**Expected:**
- Lines with no OPC mapping (B01, C01, etc.) show `source` = 'simulation'
- A01 switches to `source` = 'simulation' after staleness threshold
- No null values or errors
- Timestamps continue updating (simulation is still generating data)

**Restart OPC Studio:**
```bash
docker compose start opc-studio
```

#### 4. Verify Freshness Recovery

**After OPC restarts, query:**
```sql
SELECT line_id, source, last_ts 
FROM v_runtime_line_status 
WHERE line_id = 'A01';
```

**Expected:**
- A01 switches back to `source` = 'opc' within 1-2 minutes
- Timestamps are fresh (< 30 seconds old)

---

## Layer 4 — Diagnostics Explainability (Sprint 3)

### Objective
Validate AI-grounded diagnostics with citations, avoiding hallucinations.

### Test Steps

#### 1. Explain Line Status (A01)

**Request:**
```bash
curl -X POST http://localhost:8010/api/diagnostics/explain \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "line",
    "id": "A01"
  }'
```

**Expected Response Structure:**
```json
{
  "scope": "line",
  "id": "A01",
  "what": "Line A01 is currently operating at 78% OEE...",
  "why": "Performance loss detected due to...",
  "what_to_do": "Recommended actions:\n1. Check station ST17...",
  "checklist": [
    "Verify welding parameters",
    "Inspect material flow"
  ],
  "citations": [
    {
      "doc_id": "WLD-001",
      "title": "Welding Station Troubleshooting Guide",
      "snippet": "When cycle time exceeds..."
    }
  ],
  "runtime_available": true
}
```

**Validation Criteria:**
- All sections present: `what`, `why`, `what_to_do`, `checklist`, `citations`
- `citations` array is NOT empty (grounding required)
- Each citation has `doc_id`, `title`, `snippet`
- No invented line IDs (only A01 mentioned)
- `runtime_available` = true when OPC or simulation data exists

#### 2. Explain Station Status (ST17)

**Request:**
```bash
curl -X POST http://localhost:8010/api/diagnostics/explain \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "station",
    "id": "ST17"
  }'
```

**Expected:**
- Station-specific diagnostics
- References signals from semantic mapping (cycle_time, temperature, pressure)
- Citations from maintenance docs
- No cross-station hallucinations

#### 3. Test Runtime Unavailable Behavior

**Stop OPC Studio and wait:**
```bash
docker compose stop opc-studio
sleep 360  # Wait 6 minutes for staleness
```

**Request diagnostics:**
```bash
curl -X POST http://localhost:8010/api/diagnostics/explain \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "line",
    "id": "A01"
  }'
```

**Expected:**
```json
{
  "scope": "line",
  "id": "A01",
  "what": "Runtime data is currently unavailable for line A01.",
  "why": "OPC data is stale and simulation fallback has not yet activated.",
  "what_to_do": "Check OPC Studio connection and data pipeline.",
  "checklist": ["Verify OPC Studio health", "Check network connectivity"],
  "citations": [],
  "runtime_available": false
}
```

**Validation Criteria:**
- `runtime_available` = false
- Response acknowledges unavailability
- No fabricated OEE values or status
- No hallucinated station issues

**Restart OPC:**
```bash
docker compose start opc-studio
```

---

## Layer 5 — Regression Testing (Production Safety)

### Objective
Ensure existing functionality remains intact after Sprint 3 changes.

### Test Steps

#### 1. Verify Dashboard Pages Load

**Access via browser or curl:**
- Landing Page: http://localhost:8010/
- KPI Dashboard: http://localhost:8010/kpi-dashboard
- Live Monitoring: http://localhost:8010/live-monitoring
- Production Lines: http://localhost:8010/production-lines
- OPC Explorer: http://localhost:8010/opc-explorer
- Diagnostics Hub: http://localhost:8010/diagnostics

**Expected:**
- All pages return HTTP 200
- No JavaScript errors in browser console
- Dark industrial theme applied consistently
- Navigation drawer functional

#### 2. Test Export Endpoints

**PDF Export:**
```bash
curl -X POST http://localhost:8010/api/export/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "line_id": "A01",
    "date_from": "2025-12-20",
    "date_to": "2025-12-21"
  }' \
  --output test_export.pdf
```

**Expected:**
- Returns PDF file (non-zero size)
- No HTTP 500 errors

**CSV Export:**
```bash
curl -X POST http://localhost:8010/api/export/csv \
  -H "Content-Type: application/json" \
  -d '{
    "line_id": "A01",
    "metrics": ["oee", "availability"]
  }' \
  --output test_export.csv
```

**Expected:**
- Returns CSV file with headers
- Data includes timestamps and metric values

#### 3. Verify Database Schema Integrity

**Connect to database:**
```bash
psql -h localhost -p 5432 -U postgres -d ragdb
```

**Check production tables unchanged:**
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN (
    'oee_line_shift',
    'documents',
    'maintenance_logs',
    'downtime_events'
  );
```

**Expected:**
- All production tables exist
- No unexpected schema changes
- Continuous data simulator still writing to `oee_line_shift`

**Verify recent data:**
```sql
SELECT COUNT(*) 
FROM oee_line_shift 
WHERE date >= CURRENT_DATE - INTERVAL '1 day';
```

**Expected:**
- Count > 100 (11 lines × 3 shifts × multiple hours)
- Timestamps within last 24 hours

#### 4. Test RAG Query (Core Functionality)

**Request:**
```bash
curl -X POST http://localhost:8010/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I troubleshoot high scrap rate on welding stations?",
    "filters": {"category": "maintenance"}
  }'
```

**Expected:**
```json
{
  "answer": "To troubleshoot high scrap rate on welding stations...",
  "sources": [
    {
      "doc_id": "WLD-001",
      "title": "Welding Station Maintenance Guide",
      "relevance_score": 0.89
    }
  ],
  "confidence": "high"
}
```

**Validation:**
- Answer is coherent and grounded in sources
- Sources array not empty
- No generic/unhelpful responses

---

## Layer 6 — Performance Benchmarks (Optional)

### Objective
Establish baseline performance metrics for future regression detection.

### Test Steps

#### 1. Measure OPC Read Latency

**Tool:** `curl` with timing
```bash
time curl -X POST http://localhost:8040/opc/read \
  -H "Content-Type: application/json" \
  -d '{
    "nodeIds": ["ns=2;s=Demo.Dynamic.Scalar.Float"]
  }'
```

**Expected:**
- Response time < 500ms (typical)
- 95th percentile < 1 second

#### 2. Measure Diagnostics Response Time

```bash
time curl -X POST http://localhost:8010/api/diagnostics/explain \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "line",
    "id": "A01"
  }'
```

**Expected:**
- Response time < 5 seconds (with LLM call)
- 95th percentile < 10 seconds

#### 3. Database Query Performance

```sql
EXPLAIN ANALYZE 
SELECT * FROM v_runtime_kpi 
WHERE line_id = 'A01' 
  AND ts >= NOW() - INTERVAL '1 hour';
```

**Expected:**
- Execution time < 100ms
- Uses indexes appropriately

---

## Test Execution Log Template

| Layer | Test Case | Status | Notes | Tester | Date |
|-------|-----------|--------|-------|--------|------|
| 0 | Service Health | ☐ PASS ☐ FAIL | | | |
| 1 | OPC Connect | ☐ PASS ☐ FAIL | | | |
| 1 | OPC Browse | ☐ PASS ☐ FAIL | | | |
| 1 | OPC Read | ☐ PASS ☐ FAIL | | | |
| 1 | OPC Subscribe | ☐ PASS ☐ FAIL | | | |
| 2 | Mapping Load | ☐ PASS ☐ FAIL | | | |
| 2 | Semantic Snapshot | ☐ PASS ☐ FAIL | | | |
| 3 | Runtime Views | ☐ PASS ☐ FAIL | | | |
| 3 | Fallback Logic | ☐ PASS ☐ FAIL | | | |
| 4 | Diagnostics Line | ☐ PASS ☐ FAIL | | | |
| 4 | Diagnostics Station | ☐ PASS ☐ FAIL | | | |
| 4 | Runtime Unavailable | ☐ PASS ☐ FAIL | | | |
| 5 | Dashboard Pages | ☐ PASS ☐ FAIL | | | |
| 5 | Export Endpoints | ☐ PASS ☐ FAIL | | | |
| 5 | Database Schema | ☐ PASS ☐ FAIL | | | |
| 5 | RAG Query | ☐ PASS ☐ FAIL | | | |

---

## Troubleshooting Guide

### Issue: OPC Studio Health Fails
**Solution:**
1. Check logs: `docker compose logs opc-studio`
2. Verify OPC server is running: `netstat -an | grep 4840`
3. Restart: `docker compose restart opc-studio`

### Issue: Database Connection Errors
**Solution:**
1. Verify postgres is up: `docker compose ps shopfloor-postgres`
2. Check credentials in `.env.prod`
3. Test connection: `psql -h localhost -U postgres -d ragdb`

### Issue: Diagnostics Return Empty Citations
**Solution:**
1. Verify documents ingested: `SELECT COUNT(*) FROM documents;`
2. Check Chroma vector store: `docker compose logs shopfloor-chroma`
3. Re-ingest: `python ingest_documents.py`

### Issue: Runtime Views Empty
**Solution:**
1. Check data simulator: `docker compose ps shopfloor-data-sim`
2. Verify OEE data: `SELECT COUNT(*) FROM oee_line_shift;`
3. Check view definitions: `\d+ v_runtime_kpi` in psql

---

## Sign-Off

**QA Lead:** ________________  
**Date:** ________________  
**Status:** ☐ APPROVED ☐ CONDITIONAL ☐ REJECTED  
**Notes:**

---

**End of Test Plan**
