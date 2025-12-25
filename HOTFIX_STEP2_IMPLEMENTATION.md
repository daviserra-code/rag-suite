# HOTFIX STEP 2 - Implementation Summary

## Overview
Successfully implemented missing material evidence detection and blocking conditions for A&D and Pharma profiles.

## Changes Made

### 1. Material Context Fetching (`packages/diagnostics/explainer.py`)

#### Added Dependencies
```python
import asyncpg
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ragdb")
```

#### New Method: `_fetch_material_context()`
- Queries `v_material_evidence` view for station material context
- Returns full material evidence when row exists
- Returns default object with `evidence_present=false` when no row exists
- Determines default `mode` from domain profile (serial for A&D, lot for Pharma)

#### Integration in `explain_situation()`
- Material context is fetched and injected into `semantic_signals` for both station and line scopes
- Context is available to expectation evaluator before LLM invocation

### 2. Expectation Evaluation (`packages/diagnostics/expectation_evaluator.py`)

#### Enhanced Metrics Extraction
Added to `_extract_runtime_metrics()`:
```python
'material_evidence_present': False
'material_quality_status': None
```

#### New Blocking Rules

**Aerospace & Defence (A&D):**
- Missing evidence triggers: `"critical_station_requires_evidence"`
- Blocking condition: `"missing_material_context"`
- Additional blocking for missing serial: `"missing_serial_binding"`

**Pharma/Process:**
- Missing evidence triggers: `"zero_output_requires_batch_context"`
- Blocking condition: `"missing_batch_context"`
- HOLD/QUARANTINE status triggers: `"quality_hold_blocks_production"`
- Blocking condition: `"material_quality_hold"`
- Missing deviation with HOLD adds: `"missing_deviation_record"`

**Automotive:**
- No blocking by default (permissive)

### 3. Violation Persistence (`packages/diagnostics/explainer.py`)

#### Step 9: Persist Violations
After generating diagnostic response:
- Checks if violations or blocking conditions exist
- Uses `ViolationPersistence` to upsert violation to database
- Captures:
  - Profile context
  - Plant/line/station identifiers
  - ExpectationResult details
  - Material context snapshot
  - Timestamp reference
- Adds `violation_id` to response metadata

### 4. Semantic Snapshot API (`opc-studio/app/api.py`)

#### New Endpoint: `/semantic/snapshot`
```python
@app.get("/semantic/snapshot")
def semantic_snapshot(station: str = None):
```

**Features:**
- Accepts optional `station` query parameter for focused view
- Fetches material context from `v_material_evidence` for each station
- Returns default object with `evidence_present=false` when no DB row
- Full plant snapshot includes material context for all stations

**Response Structure:**
```json
{
  "station": "ST18",
  "material_context": {
    "mode": "serial",
    "active_serial": null,
    "quality_status": null,
    "evidence_present": false,
    ...
  }
}
```

## Database Schema (Already Exists)

### v_material_evidence View
```sql
SELECT 
  mode, active_serial, active_lot,
  work_order, operation,
  bom_revision, as_built_revision,
  quality_status,
  dry_run_authorization,
  deviation_id,
  tooling_calibration_ok,
  operator_certified,
  material_ts
FROM material_instances WHERE active = true
```

### violations Table (`sql/violation_audit_schema.sql`)
Already created in Step 3 - stores:
- Profile, plant, line, station
- Severity, blocking conditions
- violated_expectations, warnings
- material_ref, snapshot_ref
- ts_start, ts_end (NULL = active)
- requires_human_confirmation

## Verification Commands

### 1. Check ST18 Material Context (no DB row expected)
```bash
curl -s "http://localhost:8040/semantic/snapshot?station=ST18" | jq '.material_context'
```

**Expected:**
```json
{
  "mode": "serial",
  "evidence_present": false,
  "active_serial": null,
  ...
}
```

### 2. A&D Diagnostics on ST18 (should block)
```bash
curl -s -X POST http://localhost:8000/api/diagnostics/explain \
  -H "Content-Type: application/json" \
  -d '{"scope":"station","id":"ST18"}' | jq '.metadata'
```

**Expected:**
```json
{
  "blocking_conditions": ["missing_material_context", "missing_serial_binding"],
  "requires_confirmation": true,
  "severity": "critical"
}
```

### 3. Pharma HOLD Check on ST25
First insert test data:
```sql
INSERT INTO material_instances (plant, line, station, mode, active, active_serial, quality_status)
VALUES ('PLANT', 'B01', 'ST25', 'lot', true, 'BATCH-HOLD-001', 'HOLD')
ON CONFLICT (plant, line, station, mode) WHERE active = true
DO UPDATE SET quality_status = 'HOLD';
```

Then run diagnostics:
```bash
curl -s -X POST http://localhost:8000/api/diagnostics/explain \
  -H "Content-Type: application/json" \
  -d '{"scope":"station","id":"ST25"}' | jq '.metadata'
```

**Expected:**
```json
{
  "blocking_conditions": ["material_quality_hold"],
  "requires_confirmation": true,
  "severity": "critical"
}
```

### 4. Verify Violations Table
```sql
SELECT 
  station, profile, severity, 
  requires_human_confirmation,
  blocking_conditions,
  ts_start, ts_end
FROM violations 
WHERE station IN ('ST18', 'ST25')
ORDER BY ts_start DESC 
LIMIT 10;
```

**Expected:** Rows with:
- `blocking_conditions` NOT empty
- `requires_human_confirmation = true`
- `ts_end = NULL` (active violations)

## Profile-Driven Behavior

### Aerospace & Defence
- **Strict:** Missing evidence is BLOCKING
- **Serial mode:** Active serial binding required
- **Critical stations:** Must have evidence or justification

### Pharma/Process
- **Strict:** Missing batch context is BLOCKING
- **HOLD/QUARANTINE:** Production blocked immediately
- **Deviation required:** HOLD without deviation is additional violation

### Automotive/Discrete
- **Permissive:** Missing evidence generates warning only
- **Startup/changeover:** Zero output allowed
- **No blocking by default**

## Definition of Done ✅

- [x] Snapshot always includes `material_context` (even without DB row)
- [x] A&D missing evidence triggers BLOCKING conditions
- [x] Pharma HOLD triggers BLOCKING conditions
- [x] Violations persist to database after diagnostics
- [x] Automotive remains permissive by default
- [x] Logic is deterministic and profile-driven
- [x] No DB schema changes required
- [x] Verification script provided

## Files Modified

1. `packages/diagnostics/explainer.py`
   - Added `_fetch_material_context()` method
   - Injected material context into semantic signals
   - Added violation persistence (Step 9)

2. `packages/diagnostics/expectation_evaluator.py`
   - Enhanced `_extract_runtime_metrics()` with material fields
   - Added missing evidence blocking rules (A&D, Pharma)
   - Added Pharma HOLD blocking logic

3. `opc-studio/app/api.py`
   - Added `/semantic/snapshot` endpoint
   - Integrated v_material_evidence queries

## Files Created

1. `test_material_evidence_hotfix.ps1`
   - Comprehensive verification script
   - Tests all 4 deliverables
   - Automated pass/fail reporting

## Testing

Run the verification script:
```powershell
.\test_material_evidence_hotfix.ps1
```

This will:
1. Check ST18 material context exists
2. Verify A&D blocking conditions on ST18
3. Verify Pharma HOLD blocking on ST25
4. Confirm violations are persisted

## Next Steps

1. Deploy changes to production
2. Run verification script in production environment
3. Monitor violations table for new entries
4. Review blocking conditions with domain experts
5. Adjust profile expectations if needed

---

**Implementation Date:** December 25, 2025  
**Sprint:** Sprint 4 Extension - HOTFIX STEP 2  
**Status:** ✅ Complete
