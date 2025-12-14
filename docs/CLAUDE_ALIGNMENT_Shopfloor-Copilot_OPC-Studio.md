# Claude Alignment Pack — Shopfloor-Copilot + OPC Studio
## How to keep Claude 4.5 (VS Code) aligned with the architecture and implementation plan

This document is meant to live in the repo (recommended: `docs/ai/CLAUDE_ALIGNMENT.md`) and be used as the **primary context** for Claude 4.5 when generating code, refactors, or docs.

---

## 0) One-sentence north star
**Shopfloor-Copilot is an AI-ready Digital Twin Gateway for legacy manufacturing systems, combining RAG on operational knowledge with live/runtime plant context from OPC Studio (OPC UA + Historian), in an on-prem-first architecture.**

---

## 1) Project invariants (do not break)
Claude must preserve these invariants:

1. **Keep the existing OEE simulation DB** (baseline dataset) intact.
2. **OPC Studio is additive**, not a replacement:
   - OPC runtime tables remain separate (`opc_*` tables).
   - Unified access happens via *views* or *service-layer fallback*, not by overwriting simulation tables.
3. **No writeback to MES/OT in v1**. Read-only integration first.
4. **Separation of concerns**:
   - `opc-studio` is a separate service/container.
   - Shopfloor API/UI consume OPC Studio via REST and/or Postgres.
5. **On-prem-first**:
   - Local LLM (Ollama) is primary; cloud fallback only behind explicit flags.

---

## 2) Services and responsibilities
### Shopfloor-Copilot (existing)
- **UI (NiceGUI)**: user interaction, dashboards, scenario controls.
- **API (FastAPI)**: RAG Q&A, KPI tooling, integration endpoints.
- **ChromaDB**: embeddings + metadata retrieval.
- **Postgres**: operational DB (simulation + runtime/historian + derived views).

### OPC Studio (new)
- **OPC UA Server**: simulation-first plant model exposed as UA nodes.
- **REST API**: scenario control + snapshot.
- **Historian Bridge**: writes runtime samples/events into Postgres:
  - `opc_kpi_samples`
  - `opc_station_samples`
  - `opc_events`

---

## 3) Runtime data strategy (Simulation preserved + Runtime added)
We maintain two sources:

### A) Simulation baseline (keep)
- Existing OEE simulation tables and generators remain authoritative for offline history & demos.

### B) OPC runtime/historian (add)
- OPC Studio continuously writes runtime samples and events into `opc_*` tables.

### Unification (recommended)
Create views that unify both worlds without breaking either:

- `v_runtime_kpi`:
  - prefers OPC data when available and recent
  - falls back to simulation otherwise

- `v_runtime_events`:
  - merges `opc_events` with simulation downtime/event tables (if present)

**Important:** Claude should implement unification as **views or service-layer fallback**, not destructive migration.

---

## 4) Implementation order (A → B → C)
Claude should follow this sequence unless explicitly instructed otherwise:

### A) AI reads runtime context (now)
Goal: Copilot answers with live plant context + citations.

Deliverables:
- Shopfloor API endpoint (proxy): `GET /api/runtime/snapshot` → fetches OPC Studio `/snapshot`
- SQL tools:
  - `last 15/60 min KPI trend`
  - `events in time window`
- Prompt template that injects runtime context when present:
  - If snapshot available: include it
  - else: use simulation KPI baseline from DB

### B) Dashboards (after A)
Goal: KPI views built from Postgres (prefer views, not duplicated logic).
- UI cards/tables for OEE/A/P/Q trend
- event timeline (opc_events + simulation events via unified view)

### C) Plant model & scenario richness (after B)
Goal: richer `plant_model.json`, scenario composer, taxonomy and better realism.

---

## 5) Required UI: “OPC Studio” tab (MVP)
Claude should implement a task-oriented OPC Studio UI inside the existing Shopfloor UI:

MVP components:
1. **Status panel**
   - `/health`, `/historian/status` indicators
2. **Model browser**
   - `/model` shows loaded line/station IDs
3. **Live snapshot viewer**
   - tables for lines & stations (refresh button or 1–2s timer)
4. **Scenario builder**
   - dropdown Line/Station/Event, duration, impacts
   - POST `/scenario/apply`
5. **Send snapshot to Copilot**
   - fetch snapshot and prefill the chat context

Do not build a full UAExpert clone yet.

---

## 6) Coding constraints for Claude (important)
- Keep changes minimal and incremental.
- Prefer:
  - parameterized SQL
  - whitelisted queries (no arbitrary SQL execution)
  - explicit env flags
- Do not introduce heavy frameworks unless required.
- No breaking rename of existing services, ports, folders.

---

## 7) Environment variables (conventions)
Claude should read existing `.env` patterns and extend them consistently.

Recommended additions:
- `OPC_STUDIO_URL=http://opc-studio:8040`
- `RUNTIME_SOURCE=opc|sim|auto` (default `auto`)
- `RUNTIME_MAX_AGE_S=30` (if older than this, fallback)
- `HISTORIAN_ENABLED=true|false`

---

## 8) Claude prompt template (copy/paste)
Use this as the instruction header for Claude requests:

> You are working inside the Shopfloor-Copilot repository. Follow the architecture invariants:
> - Keep existing OEE simulation DB intact.
> - OPC Studio is additive (opc_* tables), unify via views or service-layer fallback.
> - No writeback to MES/OT (read-only v1).
> - opc-studio is a separate service; Shopfloor consumes it via REST + Postgres.
> Implement Phase A first: runtime snapshot proxy endpoint + prompt injection; then UI tab “OPC Studio” MVP.
> Make minimal changes, keep naming/ports stable, use parameterized SQL and whitelisted queries.

---

## 9) “Definition of Done” checks (fast)
When Claude delivers a change, validate:

1. `docker compose up -d --build` works.
2. `GET /api/runtime/snapshot` returns either:
   - OPC snapshot, or
   - clear fallback response
3. UI shows OPC Studio tab:
   - model IDs visible
   - scenario apply updates snapshot
4. Postgres receives rows in `opc_*` tables.
5. Copilot answer mentions runtime evidence + citations where applicable.

---

## 10) Optional: alignment files to add to repo
Recommended repo files:
- `docs/ai/CLAUDE_ALIGNMENT.md` (this file)
- `docs/architecture/OPC_STUDIO_STRATEGY.md` (already created earlier)
- `docs/ai/PROMPT_TEMPLATES.md` (for repeatable Claude tasks)
