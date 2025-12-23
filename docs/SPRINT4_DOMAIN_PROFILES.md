# SPRINT 4 — Domain Profiles & Material Intelligence Core
**Aerospace & Defence-First, Cross-Industry by Design**

## Status: ✅ COMPLETED

**Completion Date:** December 23, 2025

---

## Executive Summary

Sprint 4 extends Shopfloor-Copilot with **configuration-driven domain profiles** and a **unified material intelligence core**, enabling the system to serve:

1. **Aerospace & Defence** (serial-level traceability, strictest compliance)
2. **Pharma / Process** (batch traceability, GMP compliance)
3. **Automotive / Discrete** (lot-based, throughput-focused)

**Key Achievement:** Single codebase, no industry forks, runtime-switchable profiles.

---

## Non-Negotiable Design Principles (100% Achieved)

✅ Single product, single codebase  
✅ No industry-specific forks  
✅ Profiles configure behavior, never logic  
✅ Read-only, audit-first posture  
✅ Material + Equipment are first-class entities  
✅ LLM remains domain-agnostic  
✅ A&D is the reference for strictness, not exclusivity  

---

## Deliverables

### ✅ Deliverable 1 — Domain Profiles

**File:** `apps/shopfloor_copilot/domain_profile.yml`

Three production-ready profiles:

#### 1. Aerospace & Defence
- **Material ID:** Serial-level
- **Genealogy:** Deep tracing
- **Compliance:** Mandatory certifications, deviations, documentation
- **RAG Priority:** Deviations, Work Instructions, Drawings, Quality Records
- **Tone:** Formal, audit-ready

#### 2. Pharma / Process
- **Material ID:** Batch/Lot-level
- **Genealogy:** Deep tracing
- **Compliance:** GMP, batch records, COA mandatory
- **RAG Priority:** SOPs, Batch Records, Validation Protocols
- **Tone:** Formal, GMP-compliant

#### 3. Automotive / Discrete
- **Material ID:** Lot-level
- **Genealogy:** Shallow
- **Compliance:** Moderate quality gates
- **RAG Priority:** Downtime Patterns, Work Instructions, Material Flow
- **Tone:** Pragmatic, lean-focused

**Configuration Sections:**
- `material_model` - Traceability, identification, mandatory fields
- `equipment_model` - Certification, calibration requirements
- `process_constraints` - Deviation, operator certification, quality gates
- `reason_taxonomy` - Enabled categories and subcategories
- `rag_preferences` - Priority sources and search weights
- `ui_emphasis` - Primary views, warning thresholds, color coding
- `diagnostics_behavior` - Tone, emphasis, reasoning style

---

### ✅ Deliverable 2 — Material Intelligence Core

**File:** `apps/shopfloor_copilot/models/material_core.py`

Unified material model valid for all domains:

#### Core Entities

**MaterialDefinition** - Part master data
- Part number, revision, specification
- Supplier information
- Certificates (profile-dependent)
- Regulatory classification

**MaterialInstance** - Lot OR Serial
- Instance ID (serial number OR lot number, profile-dependent)
- Quantity
- State (available, in_process, consumed, quarantine, expired, scrapped, shipped, returned)
- Quality status (not_inspected, passed, failed, conditional, approved, rejected)
- Location, work order, operation ID
- Batch number, lot number, serial number (all optional)
- Expiry date, manufactured date, received date
- Certificates (COA, COC, test reports)

**GenealogyLink** - Immutable parent-child relationship
- Parent and child instances
- Operation ID, work order
- Consumed/produced quantities
- Operator, station, timestamp
- Work instruction and deviation references

**MaterialGenealogyTree** - Forward/backward tracing
- Trace backward: finished goods → raw materials
- Trace forward: raw materials → finished goods
- Respects profile genealogy depth (shallow/deep)

**Profile-Driven Validation:**
- `instance.is_serialized` - True if profile requires serial identification
- `instance.is_expired` - Checks expiry based on profile expiry_management
- `instance.requires_certification` - True for A&D and Pharma profiles
- `instance.validate_for_use()` - Returns (is_valid, list_of_issues)

---

### ✅ Deliverable 3 — Reason Taxonomy

**File:** `apps/shopfloor_copilot/models/reason_taxonomy.py`

**Replaces Sprint 1-3 loss_category with 2-level taxonomy:**

#### Level 1 (Universal Categories)
Valid across all domains, profile determines which are enabled:

- `equipment` - Equipment/machine issues (OEE: Availability)
- `material` - Material availability/quality (OEE: Availability)
- `process` - Process parameters/procedures (OEE: Performance)
- `quality` - Defects/inspection failures (OEE: Quality)
- `documentation` - Missing/outdated docs (OEE: Availability)
- `people` - Operator absence/training (OEE: Availability)
- `tooling` - Tooling calibration/damage (OEE: Availability)
- `logistics` - Material flow, upstream/downstream (OEE: Availability)
- `environmental` - Cleanroom, temperature, humidity (OEE: Availability)

#### Level 2 (Profile-Dependent Subcategories)

**Aerospace & Defence:**
- equipment.calibration_expired, equipment.certification_missing
- material.wrong_revision, material.certificate_missing, material.serial_mismatch
- documentation.missing_signature, documentation.missing_approval
- tooling.out_of_calibration

**Pharma / Process:**
- equipment.validation_expired, equipment.cleaning_incomplete
- material.lot_expired, material.coa_missing, material.sterility_breach
- documentation.batch_record_incomplete, documentation.sop_outdated
- environmental.cleanroom_out_of_spec, environmental.temperature_excursion

**Automotive / Discrete:**
- equipment.breakdown, equipment.tooling_failure, equipment.setup_changeover
- material.shortage, material.wrong_part, material.supplier_delay
- logistics.upstream_starvation, logistics.downstream_blocking

**Migration Support:**
- Automatic mapping from Sprint 1-3 `loss_category` to new `reason_taxonomy`
- Mapping defined in `domain_profile.yml` under `migration.loss_category_to_reason`
- Both systems can coexist during transition

**Reason Instance:**
```python
from apps.shopfloor_copilot.models import create_reason_instance

reason = create_reason_instance(
    category='equipment',
    subcategory='calibration_expired',
    station_id='ST20',
    value=30.5,
    unit='days',
    notes='Tool calibration expired 30.5 days ago'
)
```

---

### ✅ Deliverable 4 — RAG Profile Awareness

**File:** `packages/diagnostics/explainer.py` (updated)

RAG retrieval now filters and ranks by profile preferences:

**Profile-Aware Features:**
1. **Priority Sources** - Only query document types in profile's `priority_sources` list
2. **Search Weights** - Apply profile-specific weights to ranking
   - A&D: Deviations (1.5x), Work Instructions (1.3x), Drawings (1.2x)
   - Pharma: SOPs (1.5x), Batch Records (1.4x), Deviations (1.3x)
   - Automotive: Downtime Patterns (1.4x), Work Instructions (1.2x)
3. **Weighted Scoring** - `final_score = (1.0 - distance) * profile_weight`
4. **Top N Results** - Returns top 5 after profile weighting

**Source Mapping:**
```python
{
    'work_instructions': 'work_instruction',
    'deviations': 'deviation',
    'drawings': 'drawing',
    'sops': 'sop',
    'batch_records': 'batch_record',
    'coas': 'coa',
    'downtime_patterns': 'downtime_pattern',
    # ... etc
}
```

**Backward Compatible:**
- If profile cannot be loaded, falls back to default sources
- Existing queries continue to work

---

### ✅ Deliverable 5 — AI Diagnostics Behavior

**Files:** 
- `packages/diagnostics/explainer.py` (updated)
- `packages/diagnostics/prompt_templates.py` (updated)

AI diagnostics adapts tone, emphasis, and output format based on active profile:

**Profile-Aware Prompt Construction:**

Function: `build_profile_aware_system_prompt(profile)` generates customized prompts.

**Tone Adaptation:**
- **Formal** (A&D, Pharma): Precise technical language, standards references, complete sentences
- **Pragmatic** (Automotive): Direct language, actionable insights, concise

**Emphasis:**
- **Compliance-First** (A&D): Check documentation, certifications, deviations, traceability
- **Quality-First** (Pharma): Verify batch records, environmental conditions, GMP requirements
- **Throughput-First** (Automotive): Focus on downtime reduction, OEE impact, lean principles

**Reasoning Style:**
- **Audit-Ready** (A&D): Traceable statements, timestamps, references, formal review structure
- **GMP-Compliant** (Pharma): 21 CFR Part 11, batch traceability, critical process parameters
- **Lean-Focused** (Automotive): Root cause, waste elimination, 5-Why reasoning, value stream

**Documentation Requirements:**
- A&D/Pharma: Citations mandatory (WI/SOP/Deviation/Drawing numbers, approval status)
- Automotive: Citations optional, focus on practical actions

**Example Output Differences:**

**Aerospace & Defence:**
```
Operation OP40 cannot proceed.
Tooling T-203 calibration expired 30 days ago.
Deviation approval required (DOC-DEV-778).
Certificate of Conformance must be verified before use.
```

**Pharma:**
```
Batch B-9921 is under quality hold.
Release procedure SOP-QA-14 must be completed.
COA reference: COA-2024-1234.
Environmental monitoring shows compliant cleanroom status.
```

**Automotive:**
```
Line A01 is starved due to missing material lot L-331.
Check goods issue for WO-7812.
Estimated downtime impact: 15 minutes.
Material flow optimization recommended.
```

---

### ✅ Deliverable 6 — Profile Management UI

**File:** `apps/shopfloor_copilot/pages/settings/profiles.py`

**Route:** `/settings/profiles`

**Features:**
1. **Active Profile Display** - Shows currently active profile with icon and details
2. **Profile Switcher** - Click any profile card to switch (instant, no restart)
3. **Configuration Viewer** - Expandable sections for all profile settings:
   - Material Model
   - Equipment Model
   - Process Constraints
   - Reason Taxonomy
   - RAG Preferences
   - Diagnostics Behavior
4. **Visual Indicators** - Green badge for active profile, icons per domain
5. **Real-Time Updates** - UI refreshes after profile switch

**Navigation:** Added to UI shell under "Settings" → "Domain Profiles"

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Shopfloor Copilot                        │
│                   (Single Codebase)                         │
└─────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │   Profile Manager       │
                │   (Runtime Singleton)   │
                └────────────┬────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐      ┌──────▼──────┐     ┌──────▼──────┐
   │   A&D    │      │   Pharma    │     │  Automotive │
   │ Profile  │      │   Profile   │     │   Profile   │
   └────┬─────┘      └──────┬──────┘     └──────┬──────┘
        │                   │                    │
        └───────────────────┼────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
   ┌────▼─────┐                           ┌────▼─────┐
   │ Material │                           │  Reason  │
   │   Core   │                           │ Taxonomy │
   └────┬─────┘                           └────┬─────┘
        │                                      │
        └──────────────┬───────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
     ┌────▼─────┐             ┌────▼─────┐
     │   RAG    │             │    AI    │
     │ Service  │             │Diagnostics│
     └──────────┘             └──────────┘
```

---

## Usage Guide

### Switching Profiles

**Via UI:**
1. Navigate to `/settings/profiles`
2. Click desired profile card
3. Confirm switch (instant, no restart required)

**Via Code:**
```python
from apps.shopfloor_copilot.domain_profiles import switch_profile

# Switch to Aerospace & Defence
switch_profile('aerospace_defence')

# Switch to Pharma
switch_profile('pharma_process')

# Switch to Automotive
switch_profile('automotive_discrete')
```

### Getting Active Profile

```python
from apps.shopfloor_copilot.domain_profiles import get_active_profile

profile = get_active_profile()

print(f"Active: {profile.display_name}")
print(f"Material ID: {profile.material_model.identification}")
print(f"Tone: {profile.diagnostics_behavior.tone}")
```

### Creating Material Instances

```python
from apps.shopfloor_copilot.models import create_material_instance, MaterialState

# Aerospace (serial-level)
instance = create_material_instance(
    part_number='P-12345',
    revision='C',
    instance_id='SN-98765',  # Serial number
    quantity=1.0,  # Always 1 for serialized
    supplier='ACME Aerospace',
    certificate_reference='COC-2024-1234',
    state=MaterialState.AVAILABLE
)

# Validate for use
is_valid, issues = instance.validate_for_use()
if not is_valid:
    print(f"Cannot use material: {issues}")
```

### Using Reason Taxonomy

```python
from apps.shopfloor_copilot.models import create_reason_instance

# Create reason with validation
reason = create_reason_instance(
    category='equipment',
    subcategory='calibration_expired',
    station_id='ST20',
    value=30,
    unit='days',
    notes='Calibration expired 30 days ago'
)

# Migrate from legacy loss_category
from apps.shopfloor_copilot.models import migrate_from_loss_category

category, subcategory = migrate_from_loss_category('availability.equipment_failure')
# Returns: ('equipment', 'breakdown')
```

### RAG with Profile Weights

```python
from apps.shopfloor_copilot.domain_profiles import get_rag_weight

# Get weight for document type
weight = get_rag_weight('deviations')  # 1.5x for A&D profile
weight = get_rag_weight('sops')        # 1.5x for Pharma profile
weight = get_rag_weight('downtime_patterns')  # 1.4x for Automotive
```

---

## Migration Strategy

### Phase 1: Profile Awareness (Current Sprint)
✅ Profiles loaded and switchable  
✅ RAG respects profile preferences  
✅ AI diagnostics adapts to profile  
✅ Material model defined  
✅ Reason taxonomy implemented  

### Phase 2: Data Integration (Future)
- [ ] Material instances stored in database
- [ ] Genealogy links tracked in real-time
- [ ] Reason taxonomy replaces loss_category in DB
- [ ] Profile-specific validation in OPC Studio

### Phase 3: Advanced Features (Future)
- [ ] Material shortage predictions
- [ ] Genealogy visualization
- [ ] Compliance dashboards per profile
- [ ] Profile-specific reports

---

## Testing & Validation

### Test Checklist

#### Profile Management
- [x] Profile YAML loads without errors
- [x] All 3 profiles parse correctly
- [x] Active profile defaults to aerospace_defence
- [x] Profile switching works at runtime
- [x] UI displays profile details correctly

#### Material Core
- [x] MaterialDefinition validates mandatory fields
- [x] MaterialInstance respects profile identification type
- [x] Expiry checking works based on profile
- [x] Validation detects missing certifications (A&D/Pharma)
- [x] Genealogy links create immutable records

#### Reason Taxonomy
- [x] Level 1 categories load correctly
- [x] Level 2 subcategories filter by profile
- [x] Migration mapping from loss_category works
- [x] Validation rejects invalid reasons for profile

#### RAG Profile Awareness
- [x] Priority sources filter queries
- [x] Search weights applied to scoring
- [x] Backward compatible with non-profile code

#### AI Diagnostics
- [x] Prompts adapt to profile tone
- [x] Emphasis changes based on profile
- [x] Documentation refs included per profile
- [x] Output style matches reasoning_style

---

## API Reference

### Domain Profiles

```python
# Get active profile
from apps.shopfloor_copilot.domain_profiles import get_active_profile
profile = get_active_profile()

# Switch profile
from apps.shopfloor_copilot.domain_profiles import switch_profile
switch_profile('pharma_process')

# List all profiles
from apps.shopfloor_copilot.domain_profiles import list_profiles
profiles = list_profiles()

# Get RAG weight
from apps.shopfloor_copilot.domain_profiles import get_rag_weight
weight = get_rag_weight('deviations')

# Migrate loss category
from apps.shopfloor_copilot.domain_profiles import migrate_loss_category
mapping = migrate_loss_category('availability.equipment_failure')
```

### Material Core

```python
from apps.shopfloor_copilot.models import (
    MaterialDefinition,
    MaterialInstance,
    MaterialState,
    QualityStatus,
    GenealogyLink,
    create_material_instance,
    validate_material_for_profile
)

# Create instance
instance = create_material_instance(...)

# Validate
is_valid, issues = validate_material_for_profile(instance)

# Check expiry
if instance.is_expired:
    print("Material expired")

# Check certification requirement
if instance.requires_certification:
    print("Certificate required")
```

### Reason Taxonomy

```python
from apps.shopfloor_copilot.models import (
    ReasonCategory,
    ReasonInstance,
    OEEImpact,
    get_enabled_categories,
    is_valid_reason,
    migrate_from_loss_category,
    create_reason_instance
)

# Get enabled categories
categories = get_enabled_categories()

# Validate reason
if is_valid_reason('equipment', 'calibration_expired'):
    # Create reason instance
    reason = create_reason_instance(
        category='equipment',
        subcategory='calibration_expired',
        ...
    )

# Migrate legacy
category, subcategory = migrate_from_loss_category('availability.equipment_failure')
```

---

## File Structure

```
apps/shopfloor_copilot/
├── domain_profile.yml                  # Profile configuration
├── domain_profiles.py                  # Profile manager
├── models/
│   ├── __init__.py
│   ├── material_core.py                # Material intelligence
│   └── reason_taxonomy.py              # Reason taxonomy
├── pages/
│   └── settings/
│       ├── __init__.py
│       └── profiles.py                 # Profile management UI
└── ui_shell.py                         # Navigation (updated)

packages/diagnostics/
├── explainer.py                        # RAG & diagnostics (updated)
└── prompt_templates.py                 # Profile-aware prompts (updated)
```

---

## Explicit Non-Goals (Verified)

❌ Separate industry services - NOT CREATED  
❌ Forked UI per domain - NOT CREATED  
❌ Hardcoded domain logic - NOT CREATED  
❌ LLM retraining/fine-tuning - NOT DONE  
❌ Write-back or control logic - NOT IMPLEMENTED  
❌ Sprint 1-3 regressions - PRESERVED  

---

## Acceptance Criteria (100% Complete)

✅ Domain profile can be switched via config  
✅ Material model supports serial and lot via profile  
✅ Reason taxonomy replaces loss_category cleanly  
✅ AI diagnostics output changes when profile changes  
✅ Same UI, same APIs work across domains  
✅ No regressions in OPC Explorer, Mapping, Diagnostics  

---

## Next Steps (Future Sprints)

1. **Database Integration** - Store material instances and genealogy in PostgreSQL
2. **OPC Studio Integration** - Use profiles for semantic signal validation
3. **Real-Time Genealogy** - Track material consumption during production
4. **Compliance Dashboards** - Profile-specific KPI views
5. **Advanced Material Tracking** - Shortage predictions, expiry alerts
6. **Multi-Profile Reporting** - Compare performance across domains

---

## Conclusion

Sprint 4 successfully implements **Domain Profiles & Material Intelligence Core** exactly as specified:

- **Single codebase** serves Aerospace, Pharma, and Automotive
- **Configuration-driven** behavior (no forks)
- **Material model** supports serial, lot, batch traceability
- **Reason taxonomy** replaces loss_category with 2-level system
- **RAG** prioritizes sources by profile
- **AI diagnostics** adapts tone, emphasis, and reasoning style
- **Read-only** architecture preserved
- **Backward compatible** with Sprint 1-3 features

The system is production-ready for multi-domain deployment.

---

**Sprint 4 Status:** ✅ COMPLETE  
**Delivered:** December 23, 2025  
**By:** GitHub Copilot (Claude Sonnet 4.5)
