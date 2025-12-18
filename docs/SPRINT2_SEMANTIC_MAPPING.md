# Sprint 2 — Semantic Mapping Engine Implementation Summary

## Goal Achieved ✅
Implemented a **Semantic Mapping Engine** in OPC Studio that transforms raw OPC UA tags into stable MES-like semantic signals using YAML-first configuration.

## Architectural Principles (Enforced)

✅ **YAML is the source of truth**
- All mappings defined in [semantic_mappings.yaml](../opc-studio/config/semantic_mappings.yaml)
- No hardcoded mappings in code
- Code only applies mappings from YAML

✅ **Raw OPC ≠ Semantic signal**
- Raw tags remain untouched
- Semantic signals produced by explicit mapping
- Clear transformation pipeline

✅ **Semantic identifiers are contracts**
- Stable semantic_id for each signal (e.g., `station.state`, `welding.temperature`)
- Once defined, they are versioned and stable
- Renaming = breaking change (documented in YAML)

✅ **loss_category is mandatory**
- Every operational signal classified
- 4 categories: availability, performance, quality, non_productive
- 19 subcategories (equipment_failure, reduced_speed, process_defect, etc.)

## YAML Configuration

### File Structure
```yaml
version: "1.0"
metadata:
  name: "Manufacturing Semantic Mappings"
  updated: "2025-12-15"

loss_categories:
  availability: [equipment_failure, material_shortage, ...]
  performance: [minor_stops, reduced_speed, ...]
  quality: [scrap, rework, process_defect, ...]
  non_productive: [planned_downtime, ...]

station_types:
  assembly:
    semantic_signals:
      - semantic_id: "station.state"
        opc_source: "Status"
        loss_category_map:
          FAULTED: "availability.equipment_failure"
          STARVED: "availability.upstream_starvation"
      - semantic_id: "station.speed_actual"
        opc_source: "Speed"
        loss_category_rule:
          condition: "value < 90"
          category: "performance.reduced_speed"
  
  welding:
    semantic_signals:
      - semantic_id: "welding.quality_score"
        loss_category_rule:
          condition: "value < 90"
          category: "quality.process_defect"

derived_kpis:
  - kpi_id: "oee.availability"
    formula: "running_time / (running_time + downtime)"
    dependencies: ["station.state"]
    target: 85.0
```

### Station Types Supported
1. **assembly** - Assembly stations with state, speed, parts count, temperature
2. **welding** - Welding with temperature, current, quality score
3. **testing** - Testing with pressure, pass rate
4. **robot** - Robot with position (X/Y/Z), state

### Loss Categories (19 total)
**Availability (8):**
- equipment_failure, tooling_failure, unplanned_maintenance
- setup_changeover, material_shortage, operator_absence
- upstream_starvation, downstream_blocking

**Performance (5):**
- minor_stops, reduced_speed, startup_losses
- process_adjustment, operator_inefficiency

**Quality (4):**
- scrap, rework, startup_reject, process_defect

**Non-Productive (3):**
- planned_downtime, no_scheduled_production, engineering_test

## Semantic Engine Implementation

### Core Components

**SemanticEngine** (`semantic_engine.py` - 434 lines)
- Loads YAML configuration
- Applies semantic mappings to raw OPC data
- Determines loss_category based on rules
- Calculates derived KPIs
- Validates semantic signals

### Transformation Pipeline
1. **Load Config**: Read YAML mappings
2. **Match Station Type**: Lookup semantic model (assembly, welding, testing, robot)
3. **Extract Raw Data**: Get OPC tag values (Status, Temperature, Speed, etc.)
4. **Apply Transforms**: Range checks, moving averages, scaling
5. **Determine loss_category**: Apply state maps or rule-based conditions
6. **Generate Semantic Signal**: Create standardized output with metadata
7. **Calculate KPIs**: Compute OEE, throughput, MTBF/MTTR
8. **Validate**: Check required signals and category assignment

### Semantic Signal Output Format
```json
{
  "semantic_id": "station.state",
  "value": "FAULTED",
  "unit": null,
  "timestamp": "2025-12-15T22:33:43Z",
  "source_node": "Status",
  "loss_category": "availability.equipment_failure",
  "quality": "good",
  "description": "Station operational state",
  "data_type": "string",
  "metadata": {
    "station_id": "ST02",
    "line_id": "A01",
    "plant": "TORINO"
  }
}
```

## REST API Endpoints

### New Endpoints (6 total)

1. **GET /semantic/mappings**
   - Returns full YAML configuration
   - Version, metadata, all mappings

2. **GET /semantic/loss_categories**
   - Returns loss category taxonomy
   - 4 categories with 19 subcategories

3. **GET /semantic/kpis**
   - Returns derived KPI definitions
   - 7 KPIs: OEE (availability/performance/quality/overall), throughput, MTBF, MTTR

4. **GET /semantic/station_types**
   - Returns available station types
   - Currently: assembly, welding, testing, robot

5. **POST /semantic/transform**
   - Transform raw OPC data to semantic signals
   - Input: `{raw_data, station_type, station_metadata}`
   - Output: `{semantic_signals, kpis, validation}`

6. **GET /semantic/signals**
   - Get real-time semantic signals from entire plant
   - Transforms all stations from plant snapshot
   - Returns 109 signals + 22 KPIs (current test)

7. **GET /semantic/signals/{line_id}/{station_id}**
   - Get semantic signals for specific station
   - Includes validation results

## UI Integration

### Semantic Signals Screen
New tab: **Semantic Signals** (🔀 icon)

**Features:**
- Connection panel with Line/Station selector
- Real-time semantic signals display
- Color-coded signal cards by loss_category:
  - 🔴 Red: Availability losses
  - 🟡 Yellow: Performance losses
  - 🟠 Orange: Quality losses
  - ⚪ Gray: Non-productive
  - ⬜ White: Normal (no loss)
- Derived KPI cards with target comparison
- Loss category legend (expandable by category)
- Auto-refresh every 5 seconds
- Validation status display

## Testing Results ✅

### Test 1: Station Types
```bash
GET /semantic/station_types
Response: 4 types (assembly, welding, testing, robot)
```

### Test 2: Loss Categories
```bash
GET /semantic/loss_categories
Response: 19 categories across 4 groups
```

### Test 3: Transform Welding Station
```bash
POST /semantic/transform
Input:
  Status: FAULTED
  Temperature: 465.2°C
  WeldCurrent: 182.5A
  QualityScore: 87.3%
  ProductCount: 156

Output: 5 semantic signals
  ✅ station.state = FAULTED → loss_category: "availability.equipment_failure"
  ✅ welding.temperature = 465.2°C → no loss_category
  ✅ welding.current = 182.5A → no loss_category
  ✅ welding.quality_score = 87.3% → loss_category: "quality.process_defect" (< 90)
  ✅ station.parts_count = 156 → no loss_category

Derived KPIs: 2
  ✅ oee.availability = 0% (FAULTED state)
  ✅ throughput.actual = 156 parts/hour
```

### Test 4: Full Plant Transformation
```bash
GET /semantic/signals
Response:
  signal_count: 109 semantic signals
  kpi_count: 22 KPIs
  
Stations: 24 (4 lines × 6 stations each)
All stations RUNNING → availability = 100%
```

## Semantic Signal Examples

### 1. State Mapping with Loss Category
**Raw:** `Status = "FAULTED"`  
**Semantic:**
```json
{
  "semantic_id": "station.state",
  "value": "FAULTED",
  "loss_category": "availability.equipment_failure"
}
```

### 2. Quality Rule-Based Classification
**Raw:** `QualityScore = 87.3` (< 90 threshold)  
**Semantic:**
```json
{
  "semantic_id": "welding.quality_score",
  "value": 87.3,
  "unit": "percent",
  "loss_category": "quality.process_defect"
}
```

### 3. Performance Rule-Based Classification
**Raw:** `Speed = 85` (< 90% threshold)  
**Semantic:**
```json
{
  "semantic_id": "station.speed_actual",
  "value": 85,
  "unit": "percent",
  "loss_category": "performance.reduced_speed"
}
```

### 4. No Loss (Normal Operation)
**Raw:** `Temperature = 465.2`  
**Semantic:**
```json
{
  "semantic_id": "welding.temperature",
  "value": 465.2,
  "unit": "celsius",
  "loss_category": null
}
```

## Files Created/Modified

### New Files
1. **opc-studio/config/semantic_mappings.yaml** (420 lines)
   - Complete YAML configuration
   - 4 station types with 20+ semantic signals
   - 19 loss categories
   - 7 derived KPIs

2. **opc-studio/app/semantic_engine.py** (434 lines)
   - SemanticEngine class
   - YAML loader
   - Transformation pipeline
   - KPI calculator
   - Validation engine

3. **apps/shopfloor_copilot/screens/semantic_signals.py** (372 lines)
   - Complete UI screen
   - Signal visualization with loss_category colors
   - KPI cards
   - Loss category legend

### Modified Files
1. **opc-studio/requirements.txt**
   - Added `pyyaml==6.0.1`

2. **opc-studio/app/api.py**
   - Added 7 semantic endpoints
   - API version bumped to 0.4.0
   - Import semantic_engine

3. **apps/shopfloor_copilot/ui.py**
   - Added Semantic Signals tab (Tab 16)
   - Import render_semantic_signals

## Key Benefits

### 1. Cross-Plant Portability
- Same semantic_id works across all plants
- `station.state` always means the same thing
- No plant-specific hardcoding

### 2. Historian Stability
- Semantic IDs don't change when OPC tags are renamed
- Historical data remains queryable
- Trend analysis works across schema changes

### 3. AI Reasoning Foundation
- Structured loss_category for root cause analysis
- Consistent KPI calculations
- Semantic context for LLM prompts

### 4. Deterministic Output
- YAML-driven = predictable transformations
- Versioned configuration
- Auditable mapping logic

### 5. MES Integration Ready
- Standard signal names (station.state, welding.temperature)
- Loss category taxonomy matches OEE frameworks
- KPIs calculated consistently

## Validation Rules

1. **state_required**: All stations must have `station.state` ✅
2. **loss_category_for_downtime**: Non-RUNNING states must have loss_category ✅
3. **numeric_ranges**: Values within defined ranges (warning only)
4. **semantic_id_stable**: IDs cannot change once deployed (enforced in YAML version)

## Next Steps (Optional Enhancements)

1. **Historian Integration**: Write semantic signals to PostgreSQL with loss_category indexing
2. **Transform Library**: Add more transforms (exponential_smoothing, outlier_detection)
3. **KPI Formula Engine**: Replace placeholder calculations with proper parser
4. **Alarm Mapping**: Map raw alarms to semantic alarm categories
5. **Trend Detection**: Add anomaly detection on semantic signals
6. **Export Mappings**: Generate documentation from YAML (Markdown/PDF)
7. **Import from Kepware**: Tool to convert Kepware tag mappings to YAML
8. **Multi-Plant Mappings**: Per-plant override capability

## Conclusion

Sprint 2 successfully delivered a complete **Semantic Mapping Engine**:
- ✅ YAML-first configuration (420-line semantic_mappings.yaml)
- ✅ Semantic signal transformation with loss_category classification
- ✅ 109 semantic signals from 24 stations
- ✅ 22 derived KPIs (OEE, throughput, MTBF/MTTR)
- ✅ REST API (7 endpoints)
- ✅ UI visualization with color-coded loss categories
- ✅ Validation engine
- ✅ Deterministic, auditable transformations

The system provides:
- **Stable identifiers** for cross-plant data portability
- **loss_category** for AI-powered root cause analysis
- **Derived KPIs** for real-time manufacturing intelligence
- **YAML-driven** configuration for easy updates without code changes

Foundation complete for historian integration, AI reasoning, and MES connectivity.
