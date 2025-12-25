# Shopfloor Copilot — Demo Walkthrough Script
## Sprint 6 — Guided Demonstration

> **Duration:** 10-15 minutes  
> **Audience:** Manufacturing executives, plant managers, quality leaders  
> **Goal:** Demonstrate how Shopfloor Copilot provides credible, citation-backed guidance

---

## Pre-Demo Setup

### 1. Reset Demo State
```powershell
cd c:\Users\Davide\VS-Code Solutions\rag-suite
.\scripts\demo-reset.ps1
```

Wait for confirmation:
```
✓ Containers restarted
✓ Demo data seeded
✓ Profiles loaded: aerospace_defence (active)
Ready for demo!
```

### 2. Open Application
Navigate to: **http://localhost:8010**

### 3. Verify Profile
Check top-right corner shows:
```
🎯 Active Profile: Aerospace & Defence
```

---

## Demo Flow

### Part 1 — The Problem (3 min)

**Narrator:**
> "In modern manufacturing, especially in regulated industries like aerospace, pharma, and automotive, every production decision requires evidence. But shop floor operators are overwhelmed with hundreds of procedures, work instructions, and compliance documents."

**Show:** Navigate to Station Overview (if available) or go directly to diagnostics.

---

### Part 2 — Scenario A: Critical Evidence Missing (5 min)

#### Setup
**Station:** ST18 (Final Assembly)  
**Profile:** Aerospace & Defence

#### Step 1: Request Diagnostics
```powershell
# Or use UI: Select ST18 → "Explain Situation"
POST /api/diagnostics/explain
{
  "scope": "station",
  "id": "ST18"
}
```

#### Step 2: Read Response Aloud

**WHAT IS HAPPENING:**
> "Station ST18 is running but producing zero output. No material evidence or serial binding is present. This is a critical assembly station per AS9100D requirements."

**Pause and explain:**
- AS9100D is the aerospace quality standard
- Critical stations require full traceability
- The system detected missing evidence automatically

---

#### Step 3: WHY THIS IS HAPPENING

**Read:**
> "Missing material evidence record blocks production. Serial number binding is required before critical operations. According to **WI-OP40-Serial-Binding (rev A)**, all components must be serialized."

**Highlight the citation:**
- ✓ **WI-OP40-Serial-Binding** is a real document in the knowledge base
- ✓ Revision A is tracked
- ✓ Not generic advice — specific to this operation

---

#### Step 4: WHAT TO DO NOW

**Read:**
> "Refer to **WI-OP40-Serial-Binding (rev A)** for serial binding procedure. Verify torque wrench calibration per **CAL-T-203-Torque-Wrench (rev A)**. Complete material evidence record before proceeding."

**Key message:**
> ⚠️ **Human confirmation required before proceeding.**

**Explain:**
- System doesn't make the decision
- System provides evidence-backed guidance
- Human confirms and takes action

---

#### Step 5: Show Metadata

Scroll to metadata section:
```json
{
  "rag_documents": 5,
  "domain_profile": "Aerospace & Defence",
  "severity": "critical",
  "requires_confirmation": true,
  "blocking_conditions": [
    "missing_material_evidence",
    "missing_serial_binding"
  ]
}
```

**Point out:**
- 5 relevant documents retrieved from knowledge base
- Severity is `critical` (not AI opinion, but profile-driven)
- Blocking conditions are explicit

---

### Part 3 — Scenario B: Quality Hold (Pharma) (3 min)

#### Setup
**Switch profile** (if UI supports) or explain:
> "Now let's switch to a pharmaceutical manufacturing scenario."

**Station:** ST25 (Tablet Compression)  
**Profile:** Pharma/Process

#### Request Diagnostics
```powershell
POST /api/diagnostics/explain
{
  "scope": "station",
  "id": "ST25"
}
```

#### Highlight Key Points

**WHAT IS HAPPENING:**
> "Active lot LOT-2025-1234 is on **QUALITY HOLD**. No deviation approval present."

**WHY:**
> "According to **SOP-Deviation-Pharma-Process**, all deviations must be investigated before production resumes."

**Citations:**
- SOP-BPR-001-Tablet-Compression (Batch Production Record)
- SOP-Deviation-Pharma-Process (Deviation Management)

**Key message:**
> "Production is blocked until quality deviation is resolved."

**Explain:**
- GMP (Good Manufacturing Practice) compliance
- Quality holds must be formally resolved
- System cites the correct SOP automatically

---

### Part 4 — Scenario C: Happy Path (2 min)

#### Setup
**Station:** ST10 (Machining)  
**Profile:** Aerospace & Defence

#### Request Diagnostics
```powershell
POST /api/diagnostics/explain
{
  "scope": "station",
  "id": "ST10"
}
```

#### Highlight

**WHAT IS HAPPENING:**
> "Station ST10 is running normally. Cycle time: 30s (nominal). Good count: 45 units. Quality status: RELEASED."

**WHY:**
> "All material evidence is present and verified. According to **WI-OP35-Composite-Layup**, machining is within parameters."

**WHAT TO DO NOW:**
> "Continue normal operations. Monitor cycle time for any deviations."

**Note:** No warning, no confirmation required — calm, informative tone.

**Key message:**
> "No issues detected. Evidence is complete."

---

### Part 5 — The Value Proposition (2 min)

#### Summary Slide (if presenting) or Verbal Summary

**What We Just Saw:**

1. **Context-Aware Guidance**
   - System understands domain (aerospace vs pharma)
   - Different profiles → different expectations

2. **Citation-Backed Responses**
   - Every recommendation references a real document
   - Revisions tracked
   - Auditable trail

3. **Human-in-the-Loop**
   - System doesn't decide
   - System provides evidence
   - Human confirms and acts

4. **Deterministic Behavior**
   - Same inputs → same outputs
   - No hallucinations
   - No generic "AI answers"

---

## Q&A Preparation

### Expected Questions

**Q: "How does it know which documents to cite?"**  
**A:** "We use profile-aware RAG (Retrieval-Augmented Generation). The system:
1. Identifies the active profile (aerospace_defence, pharma_process, etc.)
2. Queries the knowledge base with profile filters
3. Retrieves the top-N most relevant documents
4. LLM synthesizes the response with mandatory citations"

---

**Q: "Can it handle custom documents?"**  
**A:** "Yes. The ingestion pipeline accepts any text-based document (PDF, TXT, MD). Documents are chunked, embedded, and stored with metadata (doc_type, profile, revision). New documents are immediately available for retrieval."

---

**Q: "What if the LLM hallucinates?"**  
**A:** "Three layers of protection:
1. **Prompt templates** enforce citation discipline
2. **RAG retrieval** ensures only real documents are referenced
3. **Metadata validation** confirms document IDs exist in the corpus"

---

**Q: "How do you ensure compliance?"**  
**A:** "Every diagnostic response includes:
- Document IDs with revisions
- Timestamp of explanation
- Violation ID for audit trail
- Profile and expectations evaluated
This creates a full audit trail for ISO/AS9100/GMP compliance."

---

**Q: "Can we customize profiles?"**  
**A:** "Yes. Profiles are YAML configuration files. You define:
- Expectations (what evidence is required)
- Reasoning priorities (documentation → people → equipment)
- Tone (formal, procedural, adaptive)
- Source preferences (SOPs, work instructions, batch records)"

---

## Post-Demo Actions

### 1. Reset for Next Demo
```powershell
.\scripts\demo-reset.ps1
```

### 2. Provide Documentation
Share:
- `docs/demo/CANONICAL_SCENARIOS.md`
- `docs/DOMAIN_PROFILES_REFERENCE.md`
- `README.md`

### 3. Schedule Follow-Up
Offer:
- Custom profile creation workshop
- Document ingestion session
- Integration planning (OPC-UA, MES, ERP)

---

## Troubleshooting

### Issue: Citations Not Appearing
**Fix:**
```powershell
# Verify RAG documents are ingested
docker exec shopfloor-copilot python -c "from packages.core_rag.chroma_client import get_collection; print(f'Documents: {get_collection().count()}')"

# Should show 100+ documents
# If 0, run ingestion:
docker exec shopfloor-copilot python scripts/ingest_mes_corpus.py
```

---

### Issue: Wrong Profile Active
**Fix:**
```powershell
# Check active profile
curl http://localhost:8010/api/profiles/active

# Switch profile (if API exists)
curl -X POST http://localhost:8010/api/profiles/activate -d '{"profile":"aerospace_defence"}'
```

---

### Issue: Station Data Missing
**Fix:**
```powershell
# Restart data simulator
docker-compose restart data-simulator

# Wait 10 seconds for OPC-UA data to populate
Start-Sleep -Seconds 10
```

---

## Success Metrics

Demo is successful if audience:
1. Understands **profile-aware reasoning**
2. Sees **citations in action**
3. Recognizes **human-in-the-loop** design
4. Asks about **customization** (profiles, documents)

---

## Appendix: Quick Reference

### API Endpoints
```
GET  /api/profiles/active          → Current profile
GET  /api/diagnostics/station/:id  → Station diagnostics
POST /api/diagnostics/explain      → Generate explanation
GET  /api/violations                → List violations
POST /api/violations/:id/acknowledge → Acknowledge violation
```

### Demo Stations
- **ST18:** Aerospace blocking (evidence missing)
- **ST25:** Pharma blocking (quality hold)
- **ST10:** Happy path (no issues)

### Document Examples
- `WI-OP40-Serial-Binding` (rev A)
- `CAL-T-203-Torque-Wrench` (rev A)
- `SOP-Deviation-Pharma-Process`
- `SOP-BPR-001-Tablet-Compression`

---

**End of Demo Script**

> **Remember:** The system is already correct. This demo makes it understandable.
