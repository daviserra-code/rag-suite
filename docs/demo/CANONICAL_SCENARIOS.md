# Canonical Demo Scenarios
## Sprint 6 — Repeatable, Credible Demonstrations

> **Core Principle:** The system is already correct. This sprint makes it understandable.

---

## Overview

Three scenarios showcase Shopfloor Copilot's value across domain profiles:
- **Scenario A:** Aerospace & Defence (Blocking - Evidence Missing)
- **Scenario B:** Pharma/Process (Blocking - Quality Hold)
- **Scenario C:** Happy Path (No Blocking)

All scenarios are deterministic and reproducible.

---

## Scenario A — Aerospace & Defence (Blocking)

### Profile
**aerospace_defence**

### Station
**ST18** (Final Assembly)

### Conditions
```json
{
  "equipment_id": "ST18",
  "state": "RUNNING",
  "cycle_time": 45,
  "good_count": 0,
  "scrap_count": 0,
  "critical": true,
  "station_type": "assembly",
  "material_evidence": null,
  "serial_binding": null,
  "quality_status": null,
  "dry_run_auth": null
}
```

### Profile Expectations (Violated)
- `critical_station_requires_evidence`: ✗ FAIL
  - Evidence: None provided
  - Required: Material evidence record + serial binding
  
- `serial_binding_before_critical`: ✗ FAIL
  - Evidence: No serial binding present
  - Required: Serial must be bound before critical operations

### Expected System Behavior

**Violation Created:**
- `severity`: `critical`
- `requires_confirmation`: `true`
- `blocking_conditions`: `["missing_material_evidence", "missing_serial_binding"]`

**RAG Citations Expected:**
- `WI-OP40-Serial-Binding` (rev A)
- `CAL-T-203-Torque-Wrench` or similar calibration procedure

**Diagnostic Response:**
```
WHAT IS HAPPENING:
- Station ST18 is running but producing zero output
- No material evidence or serial binding present
- This is a critical assembly station per AS9100D requirements

WHY THIS IS HAPPENING:
- Missing material evidence record blocks production
- Serial number binding is required before critical operations
- According to WI-OP40-Serial-Binding (rev A), all components must be serialized

WHAT TO DO NOW:
- Refer to WI-OP40-Serial-Binding (rev A) for serial binding procedure
- Verify torque wrench calibration per CAL-T-203-Torque-Wrench (rev A)
- Complete material evidence record before proceeding

⚠️ Human confirmation required before proceeding.
```

### Key Message
> **"The system blocks because evidence is missing — not because AI says so."**

The blocking is driven by:
1. Profile expectations (aerospace_defence)
2. Critical station flag
3. Missing evidence records
4. RAG-retrieved procedures

---

## Scenario B — Pharma/Process (Blocking)

### Profile
**pharma_process**

### Station
**ST25** (Tablet Compression)

### Conditions
```json
{
  "equipment_id": "ST25",
  "state": "RUNNING",
  "cycle_time": 12,
  "good_count": 0,
  "scrap_count": 3,
  "critical": true,
  "station_type": "process",
  "active_lot": "LOT-2025-1234",
  "quality_status": "HOLD",
  "deviation_id": null,
  "batch_record": null
}
```

### Profile Expectations (Violated)
- `lot_requires_batch_record`: ✗ FAIL
  - Evidence: No batch production record
  - Required: BPR with signatures
  
- `quality_hold_requires_deviation`: ✗ FAIL
  - Evidence: Quality status = HOLD, no deviation ID
  - Required: Approved deviation request

### Expected System Behavior

**Violation Created:**
- `severity`: `critical`
- `requires_confirmation`: `true`
- `blocking_conditions`: `["quality_hold_active", "missing_deviation_approval"]`

**RAG Citations Expected:**
- `SOP-BPR-001-Tablet-Compression` (Batch Production Record)
- `SOP-Deviation-Pharma-Process` (Deviation Management)

**Diagnostic Response:**
```
WHAT IS HAPPENING:
- Station ST25 is running with 3 scrap units
- Active lot LOT-2025-1234 is on QUALITY HOLD
- No deviation approval present

WHY THIS IS HAPPENING:
- Quality hold status blocks production per GMP requirements
- According to SOP-Deviation-Pharma-Process, all deviations must be investigated
- Batch production record is incomplete

WHAT TO DO NOW:
- Refer to SOP-Deviation-Pharma-Process for deviation investigation procedure
- Complete batch production record per SOP-BPR-001-Tablet-Compression
- Obtain quality approval before resuming production

⚠️ Human confirmation required before proceeding.
```

### Key Message
> **"Production is blocked until quality deviation is resolved."**

The blocking is driven by:
1. Quality hold status
2. Missing deviation approval
3. GMP compliance requirements
4. RAG-retrieved SOPs

---

## Scenario C — Happy Path (No Blocking)

### Profile
**aerospace_defence**

### Station
**ST10** (Machining)

### Conditions
```json
{
  "equipment_id": "ST10",
  "state": "RUNNING",
  "cycle_time": 30,
  "good_count": 45,
  "scrap_count": 0,
  "critical": false,
  "station_type": "machining",
  "material_evidence": {
    "doc_id": "ME-2025-1234",
    "timestamp": "2025-12-25T10:00:00Z",
    "operator": "J.Smith"
  },
  "revision_match": true,
  "quality_status": "RELEASED"
}
```

### Profile Expectations (All Pass)
- `material_evidence_present`: ✓ PASS
- `revision_matches`: ✓ PASS
- `quality_released`: ✓ PASS

### Expected System Behavior

**No Violation Created**

**RAG Citations Expected:**
- Relevant work instruction (informational only)
- No blocking procedures needed

**Diagnostic Response:**
```
WHAT IS HAPPENING:
- Station ST10 is running normally
- Cycle time: 30s (nominal)
- Good count: 45 units
- Quality status: RELEASED

WHY THIS IS HAPPENING:
- All material evidence is present and verified
- According to WI-OP35-Composite-Layup, machining is within parameters
- Revision matches engineering drawings

WHAT TO DO NOW:
- Continue normal operations
- Monitor cycle time for any deviations

No human confirmation required.
```

### Key Message
> **"No issues detected. Evidence is complete."**

The system provides:
1. Calm, informative tone
2. Relevant citations for context
3. Confirmation that operations are normal
4. No blocking or warnings

---

## Demo Reset Process

To ensure reproducibility, use the demo reset script:

```powershell
# Reset to canonical demo state
.\scripts\demo-reset.ps1

# Or manually:
docker-compose restart data-simulator
Start-Sleep -Seconds 5
docker exec shopfloor-copilot python scripts/seed_demo_violations.py --scenario canonical
```

This will:
1. Clear existing violations
2. Seed ST18, ST25, ST10 with exact conditions above
3. Reset timestamps to current time
4. Ensure deterministic output

---

## Verification

Each scenario should be tested with:

```powershell
# Test Scenario A (Aerospace Blocking)
$responseA = Invoke-RestMethod -Uri "http://localhost:8010/api/diagnostics/explain" -Method Post -Body '{"scope":"station","id":"ST18"}' -ContentType "application/json"
Write-Host "Scenario A - RAG Documents:" $responseA.metadata.rag_documents
Write-Host "Scenario A - Severity:" $responseA.metadata.severity

# Test Scenario B (Pharma Blocking)
$responseB = Invoke-RestMethod -Uri "http://localhost:8010/api/diagnostics/explain" -Method Post -Body '{"scope":"station","id":"ST25"}' -ContentType "application/json"
Write-Host "Scenario B - RAG Documents:" $responseB.metadata.rag_documents
Write-Host "Scenario B - Severity:" $responseB.metadata.severity

# Test Scenario C (Happy Path)
$responseC = Invoke-RestMethod -Uri "http://localhost:8010/api/diagnostics/explain" -Method Post -Body '{"scope":"station","id":"ST10"}' -ContentType "application/json"
Write-Host "Scenario C - RAG Documents:" $responseC.metadata.rag_documents
Write-Host "Scenario C - Severity:" $responseC.metadata.severity
```

**Expected Output:**
- Scenario A: `rag_documents >= 3`, `severity = critical`
- Scenario B: `rag_documents >= 2`, `severity = critical`
- Scenario C: `rag_documents >= 1`, `severity = null` (or info)

---

## Acceptance Criteria

Sprint 6 is DONE when:

- ✓ Same three scenarios work every time
- ✓ Output is deterministic
- ✓ Citations appear in explanations
- ✓ No new code paths introduced
- ✓ Demo can be reset in <1 minute

---

## Notes

**What This IS:**
- Documentation of existing behavior
- Repeatable demonstration scenarios
- Storytelling for domain credibility

**What This IS NOT:**
- New features
- Modified logic
- Changed expectations
- Additional validation rules

The system already works. This sprint makes it demonstrable.
