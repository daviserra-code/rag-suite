# STEP 2 & STEP 3 — Material Evidence & Violation Audit
## ✅ COMPLETE

**Date:** December 24, 2025  
**Status:** Core implementation complete, ready for integration testing

---

## STEP 2: Material Evidence Layer

### Purpose
Introduce evidence-based diagnostics with concrete, queryable material context.

### ✅ Deliverables

#### 1. Material Context Dataclass
- **File:** [packages/material_evidence/provider.py](packages/material_evidence/provider.py)
- **Class:** `MaterialContext`
- **Fields:**
  - `mode` - serial | lot
  - `active_serial` - Serial number binding
  - `active_lot` - Lot number binding
  - `work_order` - Work order reference
  - `operation` - Operation code
  - `bom_revision` - BOM revision
  - `as_built_revision` - As-built revision
  - `quality_status` - RELEASED | HOLD | QUARANTINE
  - `deviation_id` - QMS deviation reference
  - `dry_run_authorization` - Authorization flag
  - `tooling_calibration_ok` - Tooling status
  - `operator_certified` - Operator qualification

#### 2. Material Evidence Provider
- **File:** [packages/material_evidence/provider.py](packages/material_evidence/provider.py)
- **Class:** `MaterialEvidenceProvider`
- **Method:** `get_material_context(plant, line, station)`
- **Queries:**
  - `material_instances` - Serial/lot binding
  - `material_authorizations` - Dry-run auth, deviations
  - `tooling_status` - Calibration status
  - `operator_certifications` - Operator qualifications

#### 3. PostgreSQL Schema
- **File:** [sql/material_evidence_schema.sql](sql/material_evidence_schema.sql)
- **Tables:**
  - `material_instances` - Material tracking
  - `material_authorizations` - Authorizations and deviations
  - `tooling_status` - Tooling calibration
  - `operator_certifications` - Operator qualifications
- **View:** `v_material_evidence` - Consolidated evidence

#### 4. Demo Data Seeding
- **File:** [scripts/seed_demo_material_data.py](scripts/seed_demo_material_data.py)
- **Scenarios:**
  - **ST18 (A&D):** No serial, no auth → BLOCKING
  - **ST25 (Pharma):** HOLD without deviation → BLOCKING
  - **ST42 (Automotive):** Ramp-up, no material → OK
  - **ST10 (Normal):** All evidence OK → NO VIOLATIONS

#### 5. Expectation Evaluator Integration
- **File:** [packages/diagnostics/expectation_evaluator.py](packages/diagnostics/expectation_evaluator.py)
- **Enhanced:** `_extract_runtime_metrics()` now reads `material_context`
- **Updated flags:**
  - `has_serial_binding` - from `active_serial`
  - `has_batch_context` - from `active_lot`
  - `has_work_order` - from `work_order`
  - `is_declared_dry_run` - from `dry_run_authorization`
  - `has_deviation_record` - from `deviation_id`

---

## STEP 3: Violation History & Audit Trail

### Purpose
Audit-grade persistence for expectation violations with full traceability.

### ✅ Deliverables

#### 1. Violation Database Schema
- **File:** [sql/violation_audit_schema.sql](sql/violation_audit_schema.sql)
- **Table:** `violations`
  - UUID primary key
  - Profile, plant, line, station
  - Severity, ts_start, ts_end
  - `violated_expectations` (JSONB)
  - `blocking_conditions` (JSONB)
  - `warnings` (JSONB)
  - `material_ref` (JSONB)
  - `snapshot_ref` (JSONB)
  - `requires_human_confirmation` (boolean)

- **Table:** `violation_ack`
  - Acknowledgment records
  - `ack_type`: acknowledged | justified | false_positive | resolved
  - `ack_by` - user ID
  - `comment` - freetext
  - `evidence_ref` - external reference

- **Views:**
  - `v_violations_active` - Open violations with ack counts
  - `v_violations_history` - Closed violations
  - `v_violation_stats_by_station` - Aggregated statistics

#### 2. Violation Persistence Module
- **File:** [packages/violation_audit/__init__.py](packages/violation_audit/__init__.py)
- **Class:** `ViolationPersistence`
- **Methods:**
  - `upsert_violation()` - Create or update violation (no duplicates)
  - `close_violation()` - Close by ID
  - `close_violations_by_station()` - Close all for station
  - `add_acknowledgment()` - Record human ack
  - `get_active_violations()` - Query open violations
  - `get_violation_history()` - Query closed violations
  - `get_violation_by_id()` - Get single violation

#### 3. Upsert Logic (No Duplicates)
**Algorithm:**
1. Check for existing active violation with same `station` + `blocking_conditions`
2. If exists → UPDATE
3. If not exists → INSERT
4. Auto-close when `ack_type='resolved'`

**Key Feature:** Same violation never duplicated

---

## Integration Points

### Runtime Snapshot Extension
```json
{
  "station_id": "ST18",
  "good_count": 0,
  "material_context": {
    "mode": "serial",
    "active_serial": null,
    "work_order": "WO-77812",
    "dry_run_authorization": false,
    "tooling_calibration_ok": false,
    "operator_certified": false,
    ...
  }
}
```

### Diagnostics Flow with Violations
```python
# 1. Get material context
material_ctx = get_material_context(plant, line, station)

# 2. Add to runtime snapshot
snapshot['material_context'] = material_ctx.to_dict()

# 3. Evaluate expectations
result = evaluate_profile_expectations(snapshot, signals, profile)

# 4. Persist violation if blocking
if result.blocking_conditions:
    violation_id = violation_persistence.upsert_violation(
        profile=profile.name,
        plant=plant,
        line=line,
        station=station,
        expectation_result=result,
        material_context=material_ctx.to_dict(),
        snapshot_ref={"ts": snapshot['ts'], "station": station}
    )

# 5. If no longer violated, close
elif not result.blocking_conditions:
    violation_persistence.close_violations_by_station(station)
```

---

## Database Setup

### 1. Create Material Evidence Tables
```bash
psql -U postgres -d ragdb -f sql/material_evidence_schema.sql
```

### 2. Create Violation Audit Tables
```bash
psql -U postgres -d ragdb -f sql/violation_audit_schema.sql
```

### 3. Seed Demo Material Data
```bash
python scripts/seed_demo_material_data.py
```

**Expected Output:**
```
✓ ST18: No serial, no auth → BLOCKING (A&D)
✓ ST25: LOT-2025-0042 in HOLD, no deviation → BLOCKING (Pharma)
✓ ST42: No material (ramp-up) → NO BLOCKING (Automotive)
✓ ST10: SN-100234, all evidence OK → NO VIOLATIONS
```

---

## Demo Scenarios

### Scenario 1: Aerospace & Defence (ST18)
**Material Evidence:**
- ❌ No serial binding
- ❌ No dry-run authorization
- ❌ Tooling calibration overdue
- ❌ Operator certification expired

**Expected with A&D Profile:**
- `violated_expectations`: ["missing_serial_binding"]
- `blocking_conditions`: ["missing_serial_binding_is_blocking"]
- `requires_human_confirmation`: True
- `severity`: "critical"

**Violation Record:**
```sql
SELECT * FROM v_violations_active WHERE station = 'ST18';
-- Returns active blocking violation
```

### Scenario 2: Pharma (ST25)
**Material Evidence:**
- ✅ Lot binding: LOT-2025-0042
- ❌ Quality status: HOLD
- ❌ No deviation_id
- ✅ Tooling calibrated
- ✅ Operator certified

**Expected with Pharma Profile:**
- `violated_expectations`: ["quality_status_hold_requires_deviation"]
- `blocking_conditions`: ["missing_deviation_for_hold_material"]
- `requires_human_confirmation`: True

### Scenario 3: Automotive (ST42)
**Material Evidence:**
- ❌ No material (startup/ramp-up)
- ✅ Tooling calibrated
- ✅ Operator certified

**Expected with Automotive Profile:**
- `violated_expectations`: []
- `blocking_conditions`: []
- `requires_human_confirmation`: False
- `severity`: "normal"

---

## Acknowledgment Workflow

### 1. Acknowledge Violation
```python
ack_id = violation_persistence.add_acknowledgment(
    violation_id=uuid.UUID("..."),
    ack_by="supervisor_123",
    ack_type="justified",
    comment="Temporary dry-run for engineering validation",
    evidence_ref="WO-DRYRUN-2025-042"
)
```

### 2. Resolve Violation
```python
# Auto-closes violation
ack_id = violation_persistence.add_acknowledgment(
    violation_id=uuid.UUID("..."),
    ack_by="engineer_456",
    ack_type="resolved",
    comment="Serial binding completed",
    evidence_ref="SN-100234"
)
```

### 3. Query Ack History
```sql
SELECT 
    v.station,
    va.ack_by,
    va.ack_type,
    va.comment,
    va.evidence_ref,
    va.ts
FROM violations v
JOIN violation_ack va ON v.id = va.violation_id
WHERE v.station = 'ST18'
ORDER BY va.ts DESC;
```

---

## Next Steps (STEP 3 REST APIs)

### Required REST Endpoints

#### 1. GET /api/violations/active
```python
@app.get("/api/violations/active")
async def get_active_violations(
    station: Optional[str] = None,
    profile: Optional[str] = None,
    blocking_only: bool = False
):
    persistence = get_violation_persistence()
    violations = persistence.get_active_violations(station, profile, blocking_only)
    return {"violations": violations}
```

#### 2. GET /api/violations/history
```python
@app.get("/api/violations/history")
async def get_violation_history(
    station: Optional[str] = None,
    profile: Optional[str] = None,
    limit: int = 100
):
    persistence = get_violation_persistence()
    history = persistence.get_violation_history(station, profile, limit)
    return {"history": history}
```

#### 3. POST /api/violations/{id}/ack
```python
@app.post("/api/violations/{violation_id}/ack")
async def acknowledge_violation(
    violation_id: str,
    ack_by: str,
    ack_type: str,
    comment: Optional[str] = None,
    evidence_ref: Optional[str] = None
):
    persistence = get_violation_persistence()
    ack_id = persistence.add_acknowledgment(
        violation_id=uuid.UUID(violation_id),
        ack_by=ack_by,
        ack_type=ack_type,
        comment=comment,
        evidence_ref=evidence_ref
    )
    return {"ack_id": ack_id, "status": "acknowledged"}
```

#### 4. POST /api/violations/{id}/resolve
```python
@app.post("/api/violations/{violation_id}/resolve")
async def resolve_violation(
    violation_id: str,
    resolved_by: str,
    comment: Optional[str] = None
):
    persistence = get_violation_persistence()
    ack_id = persistence.add_acknowledgment(
        violation_id=uuid.UUID(violation_id),
        ack_by=resolved_by,
        ack_type="resolved",
        comment=comment
    )
    return {"ack_id": ack_id, "status": "resolved", "violation_closed": True}
```

---

## Definition of Done ✅

### STEP 2 - Material Evidence Layer
- [x] `MaterialContext` dataclass created
- [x] `MaterialEvidenceProvider` implemented
- [x] PostgreSQL schema created
- [x] Demo data seeding script created
- [x] Expectation evaluator extended to use material evidence
- [x] 4 demo scenarios seeded

### STEP 3 - Violation Audit Trail
- [x] Violation database schema created
- [x] `ViolationPersistence` class implemented
- [x] Upsert logic (no duplicates) implemented
- [x] Acknowledgment workflow implemented
- [x] Views for active/historical violations created
- [ ] REST APIs (to be added in integration phase)
- [ ] Demo violation seed data (to be added)

---

## File Inventory

```
packages/
├── material_evidence/
│   ├── __init__.py            # Package exports
│   └── provider.py            # MaterialContext, MaterialEvidenceProvider
└── violation_audit/
    └── __init__.py            # ViolationPersistence

sql/
├── material_evidence_schema.sql    # Material evidence tables + views
└── violation_audit_schema.sql      # Violation audit tables + views

scripts/
└── seed_demo_material_data.py      # Deterministic material evidence seeding
```

---

## Testing Commands

### Test Material Evidence Provider
```python
from packages.material_evidence import get_material_context

# Get material context for ST18 (should be empty/missing)
ctx = get_material_context("P001", "A01", "ST18")
print(f"Serial: {ctx.active_serial}")  # None
print(f"Auth: {ctx.dry_run_authorization}")  # False
```

### Test Violation Persistence
```python
from packages.violation_audit import get_violation_persistence
from packages.diagnostics.expectation_evaluator import ExpectationResult

persistence = get_violation_persistence()

# Create violation
result = ExpectationResult(
    violated_expectations=["missing_serial_binding"],
    blocking_conditions=["missing_serial_binding_is_blocking"],
    warnings=[],
    requires_human_confirmation=True,
    severity="critical",
    escalation_tone=True
)

violation_id = persistence.upsert_violation(
    profile="aerospace_defence",
    plant="P001",
    line="A01",
    station="ST18",
    expectation_result=result
)

print(f"Violation ID: {violation_id}")

# Query active violations
active = persistence.get_active_violations(station="ST18")
print(f"Active violations: {len(active)}")
```

---

## Regression Test Updates

Tests should be extended to include:

1. **Material Context Testing**
   - Test material evidence retrieval
   - Test profile-driven material validation
   - Test missing material scenarios

2. **Violation Persistence Testing**
   - Test upsert (no duplicates)
   - Test close violations
   - Test acknowledgment workflow

**Note:** Regression tests not yet updated (pending integration phase).

---

**Status:** ✅ STEP 2 & STEP 3 Core Implementation Complete  
**Next:** REST API implementation and integration testing  
**Ready For:** Database setup and demo scenario validation
