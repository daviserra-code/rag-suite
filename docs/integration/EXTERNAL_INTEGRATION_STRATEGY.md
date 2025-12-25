# External Integration Strategy
## Sprint 7 — Read-Only, Non-Intrusive Connectivity

---

## Core Principle

> **External systems enrich context. They never drive decisions directly.**

All external integrations are:
- **Read-only** — No write-back to external systems
- **Optional** — System works without external data
- **Enrichment** — Data supplements diagnostics, never controls outcomes
- **Disabled by default** — Must be explicitly enabled

---

## Integration Architecture

### Data Flow

```
External Systems → Context Providers → Diagnostics Engine → LLM Prompt
(SAP, PLM, QMS)     (Read-Only Adapters)   (Business Logic)   (Generation)
```

**Critical: External data flows TO diagnostics, never FROM diagnostics.**

---

## Supported Systems

### 1. SAP ERP
**Purpose:** Work order, material, and quality context

**Data Retrieved:**
- Work orders and production orders (AFPO)
- Material master data (MARA/MARC)
- Batch/lot information
- Quality notifications (QALS)
- Quality inspection lots
- PM equipment master (EQUI)
- Calibration records

**What It Enriches:**
- Material evidence context
- Quality status validation
- Work order traceability

**What It NEVER Controls:**
- Blocking decisions
- Expectation violations
- Diagnostic conclusions

**Connection Methods:**
- RFC (Remote Function Call)
- OData services
- REST APIs (SAP Cloud)

---

### 2. PLM (Product Lifecycle Management)
**Purpose:** Engineering data and design context

**Data Retrieved:**
- Engineering BOM (EBOM)
- Manufacturing BOM (MBOM)
- Part revisions and ECOs
- Engineering drawings
- Quality specifications
- Work instructions
- Process FMEAs

**What It Enriches:**
- Revision mismatch detection
- Engineering change awareness
- Design baseline verification

**What It NEVER Controls:**
- Production approval
- Quality decisions
- Blocking logic

**Supported Systems:**
- Siemens Teamcenter
- PTC Windchill
- Dassault ENOVIA
- Autodesk Fusion Lifecycle

---

### 3. QMS (Quality Management System)
**Purpose:** Quality records and compliance context

**Data Retrieved:**
- NCRs (Non-Conformance Reports)
- CAPAs (Corrective/Preventive Actions)
- Quality holds
- Deviation records
- Calibration certificates
- Audit findings
- Material certifications

**What It Enriches:**
- Quality hold awareness
- CAPA tracking
- Calibration status
- Compliance documentation

**What It NEVER Controls:**
- Quality approval
- Release decisions
- Production authorization

**Supported Systems:**
- ETQ Reliance
- MasterControl
- Arena QMS
- TrackWise

---

### 4. CMMS (Maintenance Management)
**Purpose:** Equipment health and maintenance context

**Data Retrieved:**
- Maintenance history
- Work orders (open/completed)
- Preventive maintenance schedules
- Spare parts availability
- Equipment reliability (MTBF/MTTR)
- Calibration schedules
- OEE data

**What It Enriches:**
- Maintenance due awareness
- Equipment condition context
- Downtime root cause analysis
- Reliability trends

**What It NEVER Controls:**
- Production decisions
- Maintenance scheduling
- Equipment shutdown

**Supported Systems:**
- IBM Maximo
- Infor EAM
- SAP PM
- Fiix

---

### 5. External OPC UA Servers
**Purpose:** Real-time equipment and sensor data

**Data Retrieved:**
- PLC process variables
- Sensor readings (temperature, pressure, flow)
- Vision system results
- Tool monitoring data
- Material presence sensors
- Quality measurement devices

**What It Enriches:**
- Real-time process context
- Sensor alarm awareness
- Actual vs. setpoint comparison

**What It NEVER Controls:**
- PLC logic
- Process parameters
- Equipment control

**Supported Sources:**
- PLC OPC UA servers
- SCADA systems
- DCS (Distributed Control Systems)
- IoT gateways

---

## Trust & Control Model

### For Aerospace & Defence Credibility

**External systems provide EVIDENCE, not DECISIONS.**

| Data Source | Provides | NEVER Decides |
|-------------|----------|---------------|
| SAP | Work order #, quality status | Whether to block production |
| PLM | Drawing revision, BOM | Whether revision is correct |
| QMS | NCR existence, CAPA status | Whether quality is acceptable |
| CMMS | PM due date, tool calibration | Whether maintenance is required |
| OPC UA | Sensor value, alarm state | Whether process is in control |

**The diagnostics engine evaluates external data against profile expectations.**

### Example: Quality Hold Scenario

**External Data:**
```json
{
  "sap_quality_status": "HOLD",
  "qms_ncr": "NCR-12345",
  "qms_ncr_status": "INVESTIGATION"
}
```

**Diagnostics Logic:**
1. Profile expectation: `quality_hold_requires_deviation`
2. External context confirms: Quality hold is active
3. External context confirms: NCR is under investigation
4. Diagnostic conclusion: **BLOCKING** (driven by profile, enriched by external data)

**NOT:**
- External system blocks production
- External system decides blocking is appropriate
- External system controls Shopfloor Copilot

---

## Configuration & Enablement

### Default State
**All providers are DISABLED by default.**

```yaml
# config/external_sources.yaml
sap:
  enabled: false  # Explicit enablement required
plm:
  enabled: false
qms:
  enabled: false
cmms:
  enabled: false
opcua:
  enabled: false
```

### Enabling a Provider

1. **Configuration:**
   ```yaml
   qms:
     enabled: true
     connection:
       base_url: "https://qms.company.com/api/v2"
       # API key in environment variable: QMS_API_KEY
   ```

2. **Credentials:**
   ```bash
   export QMS_API_KEY="your-api-key-here"
   export QMS_USERNAME="service-account"
   export QMS_PASSWORD="secure-password"
   ```

3. **Testing:**
   ```python
   from packages.external_context import QMSStubProvider
   
   provider = QMSStubProvider(config)
   context = provider.get_quality_context("ST18")
   print(context)  # Returns QMS data
   ```

### Graceful Degradation

**If external provider fails:**
- System logs the failure
- Diagnostics continue without external context
- No user-visible errors
- Explanation notes: "External context unavailable"

**This ensures:**
- No single point of failure
- Offline operation possible
- Resilient architecture

---

## Data Enrichment Examples

### Scenario 1: Missing Material Evidence (Aerospace)

**Without External Context:**
```
WHAT IS HAPPENING:
- Station ST18 is running with no material evidence
- Critical assembly station per AS9100D

WHY:
- Missing material evidence record
- According to WI-OP40-Serial-Binding, serial binding required

WHAT TO DO:
- Complete material evidence record
- Bind serial numbers per WI-OP40
```

**With SAP Context Enabled:**
```
WHAT IS HAPPENING:
- Station ST18 is running with no material evidence
- Work Order: WO-2025-1234 (SAP)
- Material: PN-45678 Rev B (SAP)
- Critical assembly station per AS9100D

WHY:
- Missing material evidence record for WO-2025-1234
- SAP shows work order is active but no serial binding
- According to WI-OP40-Serial-Binding, serial binding required

WHAT TO DO:
- Complete material evidence record for WO-2025-1234
- Bind serial numbers per WI-OP40
- Update SAP PP module with serial numbers
```

**Notice:** External data enriches context but doesn't change the conclusion.

---

### Scenario 2: Quality Hold (Pharma)

**Without External Context:**
```
WHAT IS HAPPENING:
- Station ST25 has quality status: HOLD
- Production blocked pending quality clearance

WHY:
- Quality hold active
- According to SOP-Deviation-Pharma-Process, deviation investigation required

WHAT TO DO:
- Complete deviation investigation
- Obtain QA approval before resuming
```

**With QMS Context Enabled:**
```
WHAT IS HAPPENING:
- Station ST25 has quality status: HOLD
- NCR-12345 active (QMS): MAJOR severity
- CAPA-567 opened (QMS): Root cause analysis in progress
- Production blocked pending quality clearance

WHY:
- Quality hold active due to NCR-12345
- QMS shows root cause: "Out-of-spec tablet hardness"
- According to SOP-Deviation-Pharma-Process, deviation investigation required
- CAPA due date: 2026-01-15

WHAT TO DO:
- Complete CAPA-567 root cause analysis
- Update NCR-12345 with corrective actions
- Obtain QA approval per SOP before resuming
- Reference: QMS deviation tracking system
```

**Notice:** QMS data adds specifics (NCR#, CAPA#, root cause) but doesn't drive the blocking decision.

---

## Security & Compliance

### Credentials Management
- **Never in config files** — Use environment variables only
- **Least privilege** — Read-only service accounts
- **Rotation** — Regular credential rotation
- **Encryption** — TLS/HTTPS for all connections

### Audit Trail
- **Query logging** — All external queries logged with timestamp
- **Data caching** — Cached responses logged
- **Failure logging** — Failed queries logged with reason
- **Audit report** — `logs/external_integration_audit.log`

### Data Privacy
- **No PII** — External providers return operational data only
- **Data retention** — Cached data expired per TTL settings
- **Access control** — Service accounts with restricted access

---

## Implementation Roadmap

### Sprint 7 (Current): Skeleton & Stubs
- ✅ Interface defined
- ✅ Stub providers created
- ✅ Configuration structure
- ✅ All providers DISABLED

### Sprint 8+: Real Integration (Future)
- Implement SAP RFC connector
- Implement PLM REST adapter
- Implement QMS API client
- Implement CMMS connector
- Test with real systems in staging

### Production Deployment
- Enable providers one at a time
- Monitor performance and reliability
- Collect feedback from operators
- Iterate on data mapping

---

## Testing Strategy

### Unit Tests
- Test each provider stub
- Verify deterministic mock data
- Test graceful degradation

### Integration Tests
- Test provider manager
- Test parallel queries
- Test timeout handling
- Test cache behavior

### End-to-End Tests
- Test diagnostics with external context
- Verify enrichment works correctly
- Confirm no decision control from external data

---

## Monitoring & Metrics

### Provider Health
- Response time (p50, p95, p99)
- Failure rate
- Timeout rate
- Cache hit rate

### Business Impact
- Enrichment value (% of diagnostics using external data)
- User satisfaction (qualitative feedback)
- False positive reduction (quantitative)

---

## Conclusion

External integrations **enrich context** without **controlling decisions**.

This architecture:
- Maintains trust (aerospace & pharma)
- Enables offline operation
- Provides graceful degradation
- Supports incremental enablement

**The system remains correct with or without external data.**

---

## Appendix: Provider Interface Summary

```python
class ExternalContextProvider:
    def get_material_context(equipment_id) → Optional[Dict]
    def get_quality_context(equipment_id) → Optional[Dict]
    def get_tooling_context(equipment_id) → Optional[Dict]
    def get_process_context(equipment_id) → Optional[Dict]
    def get_traceability_context(equipment_id) → Optional[Dict]
    
    def is_enabled() → bool
    def get_provider_name() → str
```

All methods are:
- **Read-only**
- **Optional** (return None if unavailable)
- **Non-blocking** (timeout protection)
- **Cached** (configurable TTL)

---

**Sprint 7 Status: COMPLETE**  
**All integrations: DISABLED by default**  
**System behavior: UNCHANGED**
