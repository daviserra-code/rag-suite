# Phase B Completion Report

**Date:** December 14, 2025  
**Status:** ✅ COMPLETED

## Overview

Phase B successfully integrated OPC Studio control and monitoring capabilities into the Shopfloor Copilot application, creating a unified data layer that seamlessly blends real-time OPC UA data with historical simulation data.

## Deliverables Completed

### 1. OPC Studio UI Tab
**File:** `apps/shopfloor_copilot/screens/opc_studio.py` (309 lines)

Implemented a comprehensive control panel with five main components:

#### Status Panel
- Real-time health monitoring of OPC Studio service
- Historian status indicator showing data collection state
- Refresh capability for manual updates
- Visual badges showing OK/ERROR states

#### Model Browser
- Hierarchical expansion tree showing plant structure
- Displays: Plant → Lines → Stations
- Reads from OPC Studio `/model` endpoint
- Currently showing: TORINO plant, Line A01, Stations ST17/ST18

#### Live Snapshot Viewer
- Two synchronized tables:
  - **Line Status**: Shows OEE, Availability, Performance, Quality per line
  - **Station Status**: Shows state, cycle time, and metrics per station
- Refresh button for manual updates
- Auto-converts OPC data to percentage displays

#### Scenario Builder
- Form-based interface for injecting test events
- Fields: Line ID, Station ID, Event Type, Duration, Impact Level
- Applies scenarios via POST to `/scenario/apply`
- Validation and error handling included

#### Send to Copilot
- Fetches current snapshot and displays in formatted view
- Prepares data for chat context injection
- Enables AI queries with live plant state

### 2. Unified PostgreSQL Views
**File:** `sql/create_unified_views.sql` (147 lines)

Created four strategic views that intelligently merge OPC and simulation data:

#### v_runtime_kpi
- **Purpose**: Unified KPI metrics with intelligent fallback
- **Logic**: 
  - Prefers `opc_kpi_samples` when data is recent (< 2 minutes)
  - Falls back to `oee_line_shift` for historical/simulation data
- **Columns**: line_id, ts, date, shift, oee, availability, performance, quality, total_units_produced, scrap_units, source
- **Enhancements**: 
  - Extracts date and shift from OPC timestamps for dashboard compatibility
  - Shift assignment: M (6-14h), A (14-22h), N (22-6h)
  - 30-day retention window

#### v_runtime_events
- **Purpose**: Merged event stream from OPC and simulation
- **Logic**: UNION ALL of OPC events and simulation downtime events
- **Columns**: ts, date, line_id, station_id, event_type, loss_category, severity, source, duration_min, description
- **Enhancements**: 
  - Unified schema across both data sources
  - Date extraction for time-based queries
  - 30-day retention window

#### v_runtime_line_status
- **Purpose**: Most recent status per production line
- **Logic**: Latest KPI record per line with computed status
- **Status Classification**:
  - RUNNING: availability >= 0.9
  - DEGRADED: 0.5 <= availability < 0.9
  - STOPPED: availability < 0.5
- **Use Case**: Dashboard current state indicators

#### v_runtime_events_summary
- **Purpose**: 24-hour event aggregation
- **Grouping**: By line_id, station_id, event_type, source
- **Metrics**: event_count, first_occurrence, last_occurrence, avg_downtime_min
- **Use Case**: Trend analysis and pattern detection

### 3. Dashboard KPI Integration
**File:** `apps/shopfloor_copilot/screens/kpi_dashboard_interactive.py`

Updated all seven database query functions to use unified views:

1. **get_oee_component_trends()**: `oee_line_shift` → `v_runtime_kpi`
2. **get_downtime_by_category()**: `oee_downtime_events` → `v_runtime_events`
3. **get_scrap_rate_trend()**: `oee_line_shift` → `v_runtime_kpi`
4. **get_shift_comparison()**: `oee_line_shift` → `v_runtime_kpi`
5. **get_kpi_summary()** (3 queries):
   - Average OEE: `oee_line_shift` → `v_runtime_kpi`
   - MTTR calculation: `oee_downtime_events` → `v_runtime_events`
   - Quality metrics: `oee_line_shift` → `v_runtime_kpi`

**Impact**: Dashboard now automatically shows live OPC data for Line A01 (when available) and simulation data for other lines (M10, B02, etc.)

## Technical Architecture

### Data Flow
```
OPC Studio (Port 4840/8040)
    ↓ (every 5s)
PostgreSQL opc_kpi_samples / opc_events
    ↓ (real-time preference)
Unified Views (v_runtime_kpi / v_runtime_events)
    ↓ (SQL queries)
Shopfloor Copilot Dashboard / APIs
    ↓ (NiceGUI / FastAPI)
User Interface (Port 8010)
```

### View Selection Logic
```sql
-- v_runtime_kpi logic
IF opc_kpi_samples.ts >= NOW() - 2 minutes THEN
    USE opc_kpi_samples (marked as 'opc-historian')
ELSE
    USE oee_line_shift (marked as 'simulation')
END IF
```

## Validation Results

### OPC Studio Integration
- ✅ Health endpoint: OK
- ✅ Historian: ENABLED, writing every 5 seconds
- ✅ Model loaded: TORINO/A01/ST17-ST18
- ✅ Snapshot data: Real-time OEE metrics
- ✅ Scenario application: Working

### Unified Views
```sql
-- Test query results
SELECT line_id, source, COUNT(*) FROM v_runtime_kpi GROUP BY line_id, source;

 line_id |    source     | count 
---------+---------------+-------
 A01     | opc-historian |  2836  -- Live OPC data
 M10     | simulation    |    36  -- Simulation fallback
 B02     | simulation    |    36
 C03     | simulation    |    36
```

### Dashboard Compatibility
- ✅ All 7 KPI queries updated
- ✅ Date/shift columns properly extracted
- ✅ loss_category field aligned
- ✅ No application errors after deployment

## Benefits Achieved

### 1. Seamless Data Integration
- **Single Query Interface**: Applications query unified views, unaware of underlying data source
- **Automatic Fallback**: If OPC data unavailable, simulation data serves as backup
- **Source Transparency**: 'source' column indicates origin (opc-historian vs simulation)

### 2. Operational Flexibility
- **Live Monitoring**: Real operators see actual plant data for Line A01
- **Historical Analysis**: 30-day retention for trend analysis
- **Test Scenarios**: Scenario builder enables what-if testing without disrupting real data

### 3. Scalability Foundation
- **Multi-Line Support**: Architecture ready for multiple OPC-connected lines
- **Multi-Plant Support**: Views can aggregate across TORINO, MILAN, ROME plants
- **Extension Points**: Additional views can be added for specific analytics needs

## Configuration

### Environment Variables
```bash
OPC_STUDIO_URL=http://opc-studio:8040  # Internal Docker network
RUNTIME_CONTEXT_ENABLED=true           # Phase A feature
```

### Database Connection
```python
DB_HOST=postgres
DB_PORT=5432
DB_NAME=ragdb
```

## Known Limitations

1. **Time Window**: OPC data preference limited to 2-minute window (tunable in view definition)
2. **Line Mapping**: Currently only Line A01 has OPC connection; other lines use simulation
3. **Shift Calculation**: Fixed shift hours (M: 6-14, A: 14-22, N: 22-6); doesn't account for plant-specific schedules

## Future Enhancements (Phase C Candidates)

1. **Multi-Line OPC**: Connect Lines A02, B01, C01 to OPC Studio
2. **Configurable Retention**: Make 2-minute/30-day windows configurable per deployment
3. **Advanced Status**: Add MAINTENANCE, CHANGEOVER, IDLE states beyond RUNNING/DEGRADED/STOPPED
4. **Materialized Views**: For high-frequency queries, consider materialized views with refresh schedules
5. **Alert Integration**: Trigger alerts when view queries detect anomalies

## Conclusion

Phase B successfully bridges the gap between real-time OPC UA data and historical simulation data, providing a unified, intelligent data layer. The Shopfloor Copilot application now seamlessly displays live plant status when available, with graceful degradation to simulation data for comprehensive coverage.

**All Phase B objectives achieved. Ready for Phase C expansion.**

---

**Next Phase**: See [CLAUDE_ALIGNMENT_Shopfloor-Copilot_OPC-Studio.md](./CLAUDE_ALIGNMENT_Shopfloor-Copilot_OPC-Studio.md) Phase C section for plant model expansion, scenario taxonomy, and enhanced simulation realism.
