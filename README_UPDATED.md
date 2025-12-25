# Shopfloor Copilot — AI-Powered Manufacturing Operations Platform

**Enterprise-grade RAG system for regulated manufacturing environments (Aerospace, Pharma, Automotive)**

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/yourusername/rag-suite)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Last Updated](https://img.shields.io/badge/updated-December%202025-green.svg)](CHANGELOG.md)

---

## 🎯 What is Shopfloor Copilot?

Shopfloor Copilot transforms manufacturing operations by providing **instant, evidence-backed guidance** to production operators. Instead of searching through hundreds of procedures, operators get:

✅ **Credible answers** backed by actual documentation  
✅ **Regulatory compliance** built into every response  
✅ **Domain-specific reasoning** (Aerospace ≠ Pharma ≠ Automotive)  
✅ **Citation discipline** — every recommendation shows its source  
✅ **Human-in-the-loop** — system informs, humans decide

---

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/rag-suite.git
cd rag-suite
cp .env.example .env
```

### 2. Configure Environment
Edit `.env`:
```env
# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ragdb

# Chroma Vector DB
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION=shopfloor_docs

# Ollama LLM (local or remote)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M

# Domain Profile (optional - defaults to aerospace_defence)
ACTIVE_PROFILE=aerospace_defence
```

### 3. Start Services
```bash
docker compose up -d
```

### 4. Ingest Documentation
```bash
# Ingest MES documentation corpus
docker exec shopfloor-copilot python ingest_documents.py

# Verify ingestion
curl http://localhost:8001/api/v1/collections/shopfloor_docs
```

### 5. Access Application
- **API Docs**: http://localhost:8010/docs
- **Health Check**: http://localhost:8010/health

---

## ✨ What's New (December 2025)

### 🎉 Sprint 5: RAG Collection Fix
**Status**: ✅ Complete | **Date**: Dec 23, 2025

**Problem**: RAG retrieval returning 0 documents due to collection name mismatch  
**Solution**: Standardized collection name to `shopfloor_docs`

**Changes**:
- Fixed collection name inconsistency (`rag_core` → `shopfloor_docs`)
- Enhanced debug logging with emoji markers (🔍 📚 🎯)
- Verified citations now appearing in responses

**Verification**:
```bash
pytest tests/test_rag.py -v
# ✅ RAG retrieving 5+ documents per query
# ✅ Citations: WI-OP40-Serial-Binding, CAL-T-203-Torque-Wrench
```

📖 [Sprint 5 Details](SPRINT5_IMPLEMENTATION_STATUS.md)

---

### 🎭 Sprint 6: Demo Scenarios & Walkthrough
**Status**: ✅ Complete | **Date**: Dec 23, 2025

**Goal**: Create repeatable, credible demonstrations without changing system logic

**Deliverables**:
- ✅ **3 Canonical Scenarios**: Aerospace blocking, Pharma blocking, Happy path
- ✅ **Demo Script**: 10-15 minute guided walkthrough
- ✅ **Verification Tools**: PowerShell scripts for demo reset/verify

**Key Scenarios**:

| Scenario | Profile | Station | Outcome | Key Message |
|----------|---------|---------|---------|-------------|
| **A** | Aerospace | ST18 | 🚫 BLOCKED | Missing evidence stops production |
| **B** | Pharma | ST25 | 🚫 BLOCKED | Quality HOLD requires deviation |
| **C** | Automotive | ST10 | ✅ PASS | Normal operation with guidance |

📖 [Demo Walkthrough](docs/demo/DEMO_SCRIPT.md) | [Scenarios](docs/demo/CANONICAL_SCENARIOS.md) | [Sprint 6 Summary](SPRINT6_COMPLETE.md)

---

### 🔌 Sprint 7: External Integration Skeleton
**Status**: ✅ Complete | **Date**: Dec 24, 2025

**Goal**: Prepare for future integration with ERP/PLM/QMS without integrating them yet

**Architecture**: Read-only, optional, enrichment-only — external systems provide evidence, never decisions

**Stub Providers Implemented** (All disabled by default):

| Provider | Systems Supported | Context Provided |
|----------|------------------|------------------|
| **SAP ERP** | Work orders, material, quality, PM | Material context, quality status, maintenance |
| **PLM** | Teamcenter, Windchill, ENOVIA | Part numbers, BOMs, drawings, ECOs |
| **QMS** | ETQ, MasterControl, TrackWise | NCRs, CAPAs, quality holds, calibration |
| **CMMS** | Maximo, Infor EAM, SAP PM | OEE, MTBF/MTTR, maintenance schedules |
| **External OPC UA** | PLCs, SCADA, DCS | Real-time sensor data, alarms |

**Key Files**:
```
packages/external_context/
├── interface.py           # Common ABC interface
├── sap_stub.py           # SAP ERP stub
├── plm_stub.py           # PLM stub
├── qms_stub.py           # QMS stub
├── cmms_stub.py          # CMMS stub
└── opcua_stub.py         # External OPC UA stub

config/external_sources.yaml  # All providers disabled by default
```

**Trust Model**: External systems enrich context but **never drive decisions**

📖 [Integration Strategy](docs/integration/EXTERNAL_INTEGRATION_STRATEGY.md) | [Sprint 7 Summary](docs/integration/SPRINT7_COMPLETE.md)

---

### 🛡️ Sprint 8: Regression Guards & CI
**Status**: ✅ Complete | **Date**: Dec 25, 2025

**Goal**: Ensure compliance logic never regresses, RAG never silently fails

**Deliverables**:
- ✅ **13 Regression Tests**: Profile expectations + RAG guards
- ✅ **CI Pipeline**: GitHub Actions with merge blocking
- ✅ **Documentation**: What must never break and why

**Test Coverage**:

| Area | Tests | Status |
|------|-------|--------|
| Aerospace Profile | 2 | ✅ PASS |
| Pharma Profile | 2 | ✅ PASS |
| Automotive Profile | 2 | ✅ PASS |
| Cross-Domain | 2 | ✅ PASS |
| RAG Retrieval | 5 | ⏭️ SKIP (Chroma not in CI) |

**Run Tests**:
```bash
# All regression tests
pytest tests/regression/ -v -m regression

# Specific domain
pytest tests/regression/ -v -k aerospace

# With coverage
pytest tests/regression/ --cov=packages --cov-report=html
```

**CI Pipeline**:
- Blocks merges if regression tests fail
- Runs on every PR to `main` or `develop`
- Uploads test reports and coverage artifacts

📖 [Regression Guards](docs/engineering/REGRESSION_GUARDS.md) | [CI Config](.github/workflows/ci.yml) | [Sprint 8 Summary](SPRINT8_COMPLETE.md)

---

## 🎬 Demo Walkthrough (10-15 minutes)

### Prerequisites
```bash
# 1. Ensure services are running
docker compose ps

# 2. Verify Ollama is running (local)
curl http://localhost:11434/api/tags

# 3. Check Chroma has documents
curl http://localhost:8001/api/v1/collections/shopfloor_docs

# 4. Set active profile
# Edit .env: ACTIVE_PROFILE=aerospace_defence
docker compose restart shopfloor
```

---

### Part 1: Aerospace Blocking Scenario (5 min)

**Context**: ST18 (Final Assembly) has no material evidence — a critical violation in aerospace

#### Step 1: Request Diagnostics
```bash
curl -X POST http://localhost:8010/api/diagnostics/explain \\
  -H "Content-Type: application/json" \\
  -d '{"scope":"station","id":"ST18"}'
```

#### Step 2: Observe Response

**WHAT IS HAPPENING:**
> "Station ST18 is running but producing zero output. No material evidence or serial binding is present. This is a **critical assembly station per AS9100D requirements**."

**WHY THIS IS HAPPENING:**
> "Missing material evidence record blocks production. Serial number binding is required before critical operations. According to **WI-OP40-Serial-Binding (rev A)**, all components must be serialized."

**WHAT TO DO NOW:**
> "Refer to **WI-OP40-Serial-Binding (rev A)** for serial binding procedure. Verify torque wrench calibration per **CAL-T-203-Torque-Wrench (rev A)**. Complete material evidence record before proceeding.
> 
> ⚠️ **Human confirmation required before proceeding.**"

**Key Observations**:
- ✅ **Citations present**: WI-OP40-Serial-Binding, CAL-T-203-Torque-Wrench
- ✅ **Regulatory reference**: AS9100D mentioned
- ✅ **Human-in-the-loop**: System doesn't auto-approve
- ✅ **Domain-specific**: Aerospace blocking behavior

---

### Part 2: Pharma Blocking Scenario (5 min)

**Context**: ST25 has active lot with quality HOLD status — GMP violation

#### Step 1: Switch Profile
```bash
curl -X POST http://localhost:8010/api/profile/switch \\
  -H "Content-Type: application/json" \\
  -d '{"profile":"pharma_process"}'
```

#### Step 2: Request Diagnostics
```bash
curl -X POST http://localhost:8010/api/diagnostics/explain \\
  -H "Content-Type: application/json" \\
  -d '{"scope":"station","id":"ST25"}'
```

#### Step 3: Observe Response

**WHAT IS HAPPENING:**
> "Station ST25 has active lot **LOT-2025-1234** with quality status **HOLD**. Zero output despite running state. This violates **21 CFR Part 211** GMP regulations."

**WHY THIS IS HAPPENING:**
> "Quality HOLD status prohibits production. Formal deviation request and approval required per **SOP-DEV-001-Deviation-Management (rev C)**. Lot may not be released without QA approval."

**WHAT TO DO NOW:**
> "Submit deviation request via **SOP-DEV-001-Deviation-Management (rev C)**. Obtain QA approval before proceeding. Document deviation rationale and impact assessment.
> 
> ⚠️ **Production blocked until deviation approved.**"

**Key Observations**:
- ✅ **Different blocking logic**: Pharma requires deviation approval
- ✅ **Regulatory reference**: 21 CFR Part 211 (GMP)
- ✅ **Lot traceability**: Specific lot number mentioned
- ✅ **Profile-aware reasoning**: Different from aerospace approach

---

### Part 3: Automotive Happy Path (3 min)

**Context**: ST10 running normally during production ramp-up

#### Step 1: Switch Profile
```bash
curl -X POST http://localhost:8010/api/profile/switch \\
  -H "Content-Type: application/json" \\
  -d '{"profile":"automotive_discrete"}'
```

#### Step 2: Request Diagnostics
```bash
curl -X POST http://localhost:8010/api/diagnostics/explain \\
  -H "Content-Type: application/json" \\
  -d '{"scope":"station","id":"ST10"}'
```

#### Step 3: Observe Response

**WHAT IS HAPPENING:**
> "Station ST10 is running with good output (127 units). Small scrap rate (4 units, 3.05%) within acceptable range for ramp-up phase."

**WHY THIS IS HAPPENING:**
> "Normal operation during production ramp-up. Scrap rate typical for new line startup per **IATF 16949** section 9.1.1.1. Downtime response procedures available."

**WHAT TO DO NOW:**
> "Continue monitoring. Refer to **WI-ST10-Assembly-Procedure (rev B)** for standard operating procedure. Downtime playbook available in **DT-PLB-001-Robot-Fault (rev A)** if needed."

**Key Observations**:
- ✅ **No blocking**: Automotive more lenient during ramp-up
- ✅ **Throughput focus**: Emphasizes keeping line running
- ✅ **Proactive guidance**: Provides downtime playbook preemptively
- ✅ **Different priorities**: Speed over strictness (vs aerospace/pharma)

---

### Demo Takeaways

| Aspect | Aerospace | Pharma | Automotive |
|--------|-----------|--------|------------|
| **Priority** | Safety & Traceability | GMP Compliance | Throughput & OEE |
| **Blocking** | Missing evidence | Quality HOLD | Rarely (unless critical) |
| **Approval** | Human confirmation | QA + Deviation | Operator discretion |
| **Citations** | Work instructions | SOPs + Batch records | Playbooks + Procedures |
| **Standard** | AS9100D | 21 CFR Part 211 | IATF 16949 |

**Core Message**: **Same system, different behavior based on industry requirements**

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Shopfloor Copilot                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  FastAPI     │────│ Diagnostics  │────│   Ollama     │ │
│  │   API        │    │  Explainer   │    │   LLM        │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                     │        │
│         │                    │                     │        │
│  ┌──────▼────────┐    ┌─────▼──────┐    ┌────────▼─────┐ │
│  │ Domain        │    │    RAG     │    │   ChromaDB   │ │
│  │ Profiles      │    │  Retrieval │    │   (Vectors)  │ │
│  └───────────────┘    └────────────┘    └──────────────┘ │
│         │                                                  │
│  ┌──────▼────────────────────────────────────────────┐   │
│  │         Expectation Evaluator                      │   │
│  │  (Deterministic rule-based pre-LLM checks)        │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                               │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  PostgreSQL  │    │   ChromaDB   │    │  Document    │ │
│  │   (OEE/TS)   │    │  (Embeddings)│    │   Corpus     │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Profile-Driven**: Single codebase, behavior configured by domain profile
2. **Expectation-First**: Deterministic checks before LLM invocation
3. **Citation Discipline**: RAG mandatory, every answer shows sources
4. **Human-in-the-Loop**: System informs, humans decide
5. **Read-Only Posture**: System never controls equipment or databases

---

## 📦 Project Structure

```
rag-suite/
├── apps/
│   ├── shopfloor_copilot/        # Main API application
│   │   ├── main.py               # FastAPI entry point
│   │   ├── domain_profiles.py    # Profile management
│   │   └── routes/               # API endpoints
│   └── opc-studio/               # OPC UA historian (optional)
│
├── packages/
│   ├── diagnostics/              # Core diagnostics logic
│   │   ├── explainer.py          # Main diagnostics explainer
│   │   └── expectation_evaluator.py  # Pre-LLM rule checks
│   ├── core_rag/                 # RAG retrieval
│   │   ├── chroma_client.py      # ChromaDB client
│   │   └── retrieval.py          # Vector search + reranking
│   ├── core_ingest/              # Document ingestion
│   │   └── ingest_pipeline.py    # PDF/Word → Chroma
│   └── external_context/         # External system stubs (Sprint 7)
│       ├── interface.py          # Common ABC interface
│       ├── sap_stub.py           # SAP ERP stub
│       ├── plm_stub.py           # PLM stub
│       ├── qms_stub.py           # QMS stub
│       ├── cmms_stub.py          # CMMS stub
│       └── opcua_stub.py         # External OPC UA stub
│
├── tests/
│   ├── regression/               # Sprint 8 regression guards
│   │   ├── test_expectations_deterministic.py
│   │   └── test_rag_non_empty.py
│   └── test_rag.py              # RAG retrieval tests
│
├── data/
│   └── documents/                # MES documentation corpus
│       ├── work_instructions/
│       ├── calibration_procedures/
│       ├── sops/
│       └── maintenance_playbooks/
│
├── config/
│   └── external_sources.yaml     # External integration config
│
├── docs/
│   ├── demo/                     # Sprint 6 demo materials
│   │   ├── DEMO_SCRIPT.md
│   │   └── CANONICAL_SCENARIOS.md
│   ├── engineering/              # Sprint 8 engineering docs
│   │   └── REGRESSION_GUARDS.md
│   └── integration/              # Sprint 7 integration docs
│       └── EXTERNAL_INTEGRATION_STRATEGY.md
│
├── .github/
│   └── workflows/
│       └── ci.yml                # Sprint 8 CI pipeline
│
├── docker-compose.yml            # Multi-service orchestration
├── Dockerfile                    # Shopfloor Copilot container
├── requirements.txt              # Python dependencies
├── ingest_documents.py           # Document ingestion script
├── pytest.ini                    # Pytest configuration
└── .env                          # Environment configuration
```

---

## 🔧 Configuration

### Domain Profiles

Located in: `apps/shopfloor_copilot/domain_profiles.py`

**Available Profiles**:
- `aerospace_defence` - AS9100D compliance, strict evidence requirements
- `pharma_process` - GMP (21 CFR Part 211), batch/lot focus
- `automotive_discrete` - IATF 16949, throughput optimization

**Switch Profile**:
```bash
# Via API
curl -X POST http://localhost:8010/api/profile/switch \\
  -H "Content-Type: application/json" \\
  -d '{"profile":"pharma_process"}'

# Via Environment Variable
# Edit .env: ACTIVE_PROFILE=pharma_process
docker compose restart shopfloor
```

---

### External Integration Configuration

Located in: `config/external_sources.yaml`

**Example**:
```yaml
sap:
  enabled: false  # Set to true when ready
  connection:
    type: "RFC"
    host: "sap.example.com"
    port: 3300
  timeout_seconds: 30
  retry_attempts: 3

plm:
  enabled: false
  connection:
    type: "REST"
    base_url: "https://plm.example.com/api"
  auth:
    type: "oauth2"

# ... qms, cmms, opcua configs
```

**All providers disabled by default** — enable when ready to integrate

---

## 🧪 Testing

### Run All Tests
```bash
pytest -v
```

### Regression Tests Only
```bash
pytest tests/regression/ -v -m regression
```

### RAG Retrieval Tests
```bash
pytest tests/test_rag.py -v
```

### With Coverage
```bash
pytest --cov=packages --cov-report=html
open htmlcov/index.html
```

### CI Status
Tests run automatically on every PR to `main` or `develop`. View results:
```bash
gh pr checks <pr-number>
```

---

## 📚 Documentation Index

### Core Documentation
- **[Demo Walkthrough](docs/demo/DEMO_SCRIPT.md)** - 10-15 minute guided demo
- **[Canonical Scenarios](docs/demo/CANONICAL_SCENARIOS.md)** - Repeatable test scenarios
- **[Domain Profiles](docs/SPRINT4_DOMAIN_PROFILES.md)** - Profile configuration guide
- **[Regression Guards](docs/engineering/REGRESSION_GUARDS.md)** - What must never break

### Sprint Documentation
- **[Sprint 5: RAG Fix](SPRINT5_IMPLEMENTATION_STATUS.md)** - Collection name fix
- **[Sprint 6: Demo Scenarios](SPRINT6_COMPLETE.md)** - Demo materials
- **[Sprint 7: External Integration](docs/integration/EXTERNAL_INTEGRATION_STRATEGY.md)** - Integration skeleton
- **[Sprint 8: Regression Tests](SPRINT8_COMPLETE.md)** - CI & tests

### Integration Guides
- **[External Integration Strategy](docs/integration/EXTERNAL_INTEGRATION_STRATEGY.md)** - SAP/PLM/QMS integration
- **[OPC UA Explorer](docs/SPRINT1_OPC_EXPLORER.md)** - OPC UA integration
- **[Jira Integration](docs/JIRA_INTEGRATION.md)** - Ticket tracking

### Deployment
- **[Hetzner Deployment](docs/HETZNER_DEPLOYMENT.md)** - Production deployment guide
- **[Backup & Restore](docs/BACKUP_RESTORE.md)** - Data management

---

## 🚀 Production Deployment

### Environment Variables

**Required**:
```env
DATABASE_URL=postgresql://user:pass@postgres:5432/ragdb
CHROMA_HOST=localhost
CHROMA_PORT=8001
OLLAMA_BASE_URL=http://localhost:11434
```

**Optional**:
```env
ACTIVE_PROFILE=aerospace_defence
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M
LOG_LEVEL=INFO
```

### Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| `shopfloor` | 8010 | Main API application |
| `postgres` | 15432 | Time-series database |
| `chroma` | 8001 | Vector database |
| `opc-studio` | 8040 | OPC UA historian (optional) |

### Health Checks

```bash
# Shopfloor API
curl http://localhost:8010/health

# Chroma DB
curl http://localhost:8001/api/v1/heartbeat

# PostgreSQL
docker exec shopfloor-postgres pg_isready -U postgres
```

---

## 🤝 Contributing

### Branching Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature branches
- `hotfix/*` - Emergency fixes

### Commit Messages
Follow conventional commits:
```
feat: Add pharma profile expectations
fix: Correct RAG collection name
docs: Update demo walkthrough
test: Add aerospace blocking scenario
```

### Pull Request Process
1. Create feature branch from `develop`
2. Make changes and add tests
3. Run regression tests: `pytest tests/regression/ -v -m regression`
4. Push and create PR to `develop`
5. Wait for CI to pass (required)
6. Request review from maintainers

---

## 📊 Performance

| Metric | Target | Actual |
|--------|--------|--------|
| RAG Query | < 1s | ~500ms |
| Diagnostics Explain | < 2s | ~1.2s |
| Profile Switch | < 100ms | ~50ms |
| Test Suite | < 30s | ~10s |
| Collection Ingest (40 docs) | < 5min | ~3min |

---

## 🛟 Support

### Common Issues

**Issue**: Tests skip with "Collection not found"  
**Solution**: Ingest documents first: `python ingest_documents.py`

**Issue**: Ollama connection refused  
**Solution**: Start Ollama: `ollama serve` (or check `OLLAMA_BASE_URL`)

**Issue**: Chroma connection refused  
**Solution**: Check port mapping in `.env` (should be 8001 for external access)

**Issue**: No citations in responses  
**Solution**: Verify collection exists: `curl http://localhost:8001/api/v1/collections/shopfloor_docs`

### Contact
- **Issues**: [GitHub Issues](https://github.com/yourusername/rag-suite/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/rag-suite/discussions)

---

## 📄 License

Proprietary - All Rights Reserved

---

## 🙏 Acknowledgments

Built for regulated manufacturing environments with love by the Shopfloor Copilot team.

**Standards Referenced**:
- AS9100D (Aerospace Quality Management)
- 21 CFR Part 211 (GMP for Pharmaceuticals)
- IATF 16949 (Automotive Quality Management)

---

**Version**: 2.1.0  
**Last Updated**: December 25, 2025  
**Status**: Production Ready ✅
