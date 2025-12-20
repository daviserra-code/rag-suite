# Sprint 3 — AI-Grounded Diagnostics & Explainability

## Goal (non-negotiable)
Implement **AI-driven, explainable diagnostics** that transform **semantic runtime data** into **clear, justified, and actionable explanations**, without impacting existing production analytics.

Sprint 3 turns Shopfloor-Copilot into a real **AI MES Companion**.

The AI must:
- reason from **runtime evidence**
- use **loss_category** as the primary diagnostic axis
- ground recommendations in **retrieved knowledge (RAG)**
- clearly separate **facts, reasoning, and actions**

This sprint is **read-only** with respect to runtime, historian, and production KPIs.

---

## Architectural Context (must be respected)

Sprint 3 builds on:

- **Sprint 1**: OPC Explorer (UAExpert-like)
- **Sprint 2**: Semantic Mapping Engine (Kepware-like, YAML-first)
- **Phase B**: Unified runtime + simulation views already in production

Sprint 3 MUST NOT:
- alter existing OEE simulation tables
- alter Phase B dashboards or exports
- write to historian
- control or modify runtime state

---

## Core Concept

### From (traditional MES)
> “Line A01 OEE is low.”

### To (AI MES Companion)
> “Line A01 OEE degradation is currently associated with station ST17 in FAULTED state,  
> classified as availability.equipment_failure.  
> Similar conditions require mechanical inspection and sensor reset  
> (Maintenance WI-23, SOP-MNT-02).”

The AI must **explain what is happening, why, and what to do**, with evidence.

---

## Authoritative Inputs to the AI

### 1) Semantic Runtime Snapshot (Authoritative Truth)

Source:

The snapshot includes:
- plant
- line
- station(s)
- semantic signals
- KPI values
- loss_category classification

Example (simplified):

```json
{
  "plant": "TORINO",
  "line": "A01",
  "stations": {
    "ST17": {
      "state": "FAULTED",
      "loss_category": "availability.equipment_failure"
    }
  },
  "line_kpis": {
    "availability": 0.0,
    "performance": 0.92,
    "quality": 0.98,
    "oee": 0.0
  }
}

This snapshot is the single source of runtime truth for Sprint 3.

2) Loss Context (Derived, Not Invented)

From the snapshot, the system derives:

active loss_category

impacted role:

availability

performance

quality

affected scope:

line

station

Loss context is never inferred heuristically.

3) Knowledge Base (RAG via Chroma)

Used ONLY for:

procedures

explanations

corrective actions

safety / quality steps

Typical documents:

Work Instructions (WI)

SOPs

Maintenance tickets

Quality alerts

RAG must never override runtime facts.

New Copilot Capability
Feature Name

Explain Situation

Trigger

From UI or API:

User selects:

a line (e.g. A01)

or a station (e.g. ST17)

User clicks:

Explain this situation

API Implementation
New Endpoint
POST /api/diagnostics/explain


Request body:

{
  "scope": "line | station",
  "id": "A01 | ST17"
}

Endpoint Behavior (Mandatory Flow)

Fetch semantic runtime snapshot

Extract scope-specific context

Identify active loss_category

Query Chroma using:

loss_category

equipment keywords

line / station metadata

Build a structured prompt

Call the LLM

Return structured explanation

If snapshot is unavailable or stale:

explicitly state “runtime data unavailable”

do NOT invent values

Prompt Structure (Mandatory)

The LLM system prompt MUST enforce the following structure.

Section 1 — What is happening (runtime evidence)

cite semantic signals

cite KPIs

cite loss_category

no interpretation

Section 2 — Why this is happening (reasoned explanation)

correlate evidence with loss_category

apply domain reasoning

state uncertainty if data is insufficient

Section 3 — What to do now (procedures)

retrieve relevant WI/SOP via RAG

include document citations

prioritize safety and quality

Section 4 — What to check next (checklist)

short, actionable steps

ordered by priority

derived from procedures and runtime context

Guardrails (Strict)

The AI MUST:

reference ONLY line/station IDs present in the snapshot

NEVER invent signals, values, or causes

clearly separate facts from recommendations

explicitly state lack of data when applicable

avoid probabilistic language unless justified

The AI MUST NOT:

speculate beyond evidence

reference other lines/stations implicitly

recommend actions implying write-back or control

UI Requirements

In Shopfloor-Copilot UI (OPC / Runtime context):

Button: Explain this situation

Output panel with four sections:

What is happening

Why

What to do

Checklist

UI styling is secondary to correctness and clarity.

What NOT to Implement in This Sprint

Claude must NOT:

write semantic data to historian

auto-trigger actions or alarms

generate or modify mappings

alter loss taxonomy

introduce ML anomaly detection

change existing dashboards

Acceptance Criteria (Definition of Done)

Sprint 3 is complete when:

Selecting a line or station returns a structured explanation

Explanation is grounded in:

semantic runtime snapshot

loss_category

RAG citations

No hallucinated identifiers appear

Missing data is explicitly acknowledged

Phase B dashboards and exports remain untouched

Why This Sprint Matters

After Sprint 3:

OPC Studio = UAExpert + Kepware

Shopfloor-Copilot = AI MES Companion

AI output is:

explainable

auditable

operationally useful

This sprint marks the transition from monitoring to decision support.
