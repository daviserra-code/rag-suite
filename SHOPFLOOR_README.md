# Shopfloor Copilot - AI MES Companion

## Overview

Shopfloor Copilot is an AI-powered assistant that integrates with legacy MES systems (like Siemens Opcenter Execution) to help manufacturing personnel optimize operations through intelligent Q&A, guided procedures, and data-driven insights.

## Key Features

### ✅ Implemented (Phase 1)

1. **Ollama LLM Integration**
   - Local LLM execution (privacy-first, on-premises)
   - Role-specific prompts (Operator, Line Manager, Quality Manager, Plant Manager)
   - Streaming and non-streaming responses
   - Cloud fallback option (configurable)

2. **Enhanced RAG with MES Context**
   - Metadata-aware retrieval filtering by:
     - Plant, Line, Station, Shift (Turno)
     - Document type, revision, validity dates
     - Safety tags, language
   - Vector search + CrossEncoder reranking
   - Citation tracking with source documents

3. **Interactive Operator Q&A**
   - Real-time chat interface
   - Context filters for targeted results
   - Suggested questions
   - Source citations with confidence scores

4. **Document Ingestion with MES Metadata**
   - PDF processing with chunking
   - Rich metadata capture (plant, line, station, etc.)
   - Version control (rev, valid_from/to)
   - Safety classification tags

### 🚧 Coming Soon (Phase 2)

- KPI Dashboard with OEE/FPY/MTTR metrics
- SQL KPI Tool for read-only MES data queries
- Hybrid retrieval (BM25 + vector + reranking)
- Guided checklist generation from WI documents
- Ticket similarity search and root-cause analysis
- Mock MES schemas with A01 line pilot data

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Shopfloor Copilot                     │
│                     (Port 8010)                          │
├─────────────────────────────────────────────────────────┤
│  UI Layer (NiceGUI)                                     │
│  ├─ Operator Q&A (Interactive Chat)                    │
│  ├─ Operations Dashboard                               │
│  ├─ Checklists & Step Guides                           │
│  └─ Ticket Insights                                     │
├─────────────────────────────────────────────────────────┤
│  API Layer (FastAPI)                                    │
│  ├─ /api/ask (legacy extractive)                       │
│  ├─ /api/ask/llm (Ollama-powered)                      │
│  ├─ /api/ingest (with MES metadata)                    │
│  └─ /api/health/ollama                                  │
├─────────────────────────────────────────────────────────┤
│  Core RAG Engine                                        │
│  ├─ Retriever (vector + metadata filters)              │
│  ├─ Reranker (CrossEncoder)                            │
│  ├─ LLM Client (Ollama)                                │
│  └─ Embeddings (SentenceTransformers)                  │
├─────────────────────────────────────────────────────────┤
│  Data Layer                                             │
│  ├─ ChromaDB (vector store)                            │
│  └─ PostgreSQL (MES data replica)                      │
└─────────────────────────────────────────────────────────┘
         │                               │
         ▼                               ▼
    Ollama LLM                    Legacy MES System
  (localhost:11434)            (Siemens Opcenter, etc.)
```

## Quick Start

### 1. Prerequisites

```bash
# Install Ollama
# Visit: https://ollama.ai

# Pull a model
ollama pull llama3.2
```

### 2. Environment Setup

```bash
# Copy and configure environment
cp .env.example .env

# Key settings:
# OLLAMA_BASE_URL=http://localhost:11434          # Local Ollama
# OLLAMA_BASE_URL=http://host.docker.internal:11434  # From Docker
# OLLAMA_MODEL=llama3.2:latest
# ENABLE_RERANK=true
# ENABLE_CLOUD_FALLBACK=false
```

### 3. Start Services

```bash
# With Docker Compose
docker compose up --build

# Or locally for development
uvicorn apps.shopfloor_copilot.main:app --host 0.0.0.0 --port 8010 --reload
```

### 4. Access the UI

- **Shopfloor Copilot**: http://localhost:8010
- **API Docs**: http://localhost:8010/docs

### 5. Test the Integration

```bash
python test_shopfloor.py
```

## API Usage Examples

### Ask with Ollama LLM

```bash
curl -X POST http://localhost:8010/api/ask/llm \
  -H "Content-Type: application/json" \
  -d '{
    "app": "shopfloor_copilot",
    "query": "How do I start Line A01?",
    "filters": {
      "line": "A01",
      "plant": "P01"
    },
    "role": "operator",
    "use_llm": true
  }'
```

### Ingest Document with MES Metadata

```bash
curl -X POST http://localhost:8010/api/ingest \
  -F "app=shopfloor_copilot" \
  -F "doctype=WI" \
  -F "plant=P01" \
  -F "line=A01" \
  -F "station=S110" \
  -F "rev=v1.2" \
  -F "safety_tag=critical" \
  -F "lang=en" \
  -F "file=@work_instruction_A01.pdf"
```

### Check Ollama Health

```bash
curl http://localhost:8010/api/health/ollama
```

## MES Context Metadata

All documents support these metadata fields for precise filtering:

| Field | Description | Example |
|-------|-------------|---------|
| `plant` | Plant identifier | "P01" |
| `line` | Production line | "A01", "B02" |
| `station` | Work station | "S110", "S120" |
| `turno` | Shift identifier | "T1", "T2", "T3" |
| `doctype` | Document type | "WI", "SOP", "EWI", "manual" |
| `rev` | Document revision | "v1.2", "R3" |
| `valid_from` | Validity start date | "2025-01-01" |
| `valid_to` | Validity end date | "2025-12-31" |
| `safety_tag` | Safety classification | "critical", "standard" |
| `lang` | Language code | "en", "it", "de" |

## Role-Specific Prompts

The system adapts responses based on user role:

- **Operator**: Step-by-step procedures, safety focus, operational clarity
- **Line Manager**: Performance insights, bottlenecks, resource optimization
- **Quality Manager**: Defect analysis, quality procedures, root causes
- **Plant Manager**: Strategic KPIs, trends, cross-functional recommendations

## Configuration Reference

### Environment Variables

```bash
# Ollama LLM
OLLAMA_BASE_URL=http://localhost:11434    # Ollama endpoint
OLLAMA_MODEL=llama3.2:latest              # Model to use
ENABLE_CLOUD_FALLBACK=false               # Cloud LLM fallback

# RAG Configuration
ENABLE_RERANK=true                        # Use CrossEncoder reranking
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-12-v2

# Data Sources
CHROMA_HOST=chroma                        # Vector DB
CHROMA_PORT=8000
POSTGRES_HOST=postgres                    # MES data replica
POSTGRES_DB=ragdb

# SQL KPI Tool (Phase 2)
SQL_KPI_ENABLED=true
POSTGRES_REPLICA_HOST=postgres
```

## Development

### Project Structure

```
apps/shopfloor_copilot/
├── main.py                          # FastAPI app entry point
├── ui.py                            # NiceGUI UI orchestration
├── theme.py                         # Design system tokens
├── routers/
│   ├── ask.py                       # Q&A endpoints
│   ├── ingest.py                    # Document ingestion
│   └── export.py                    # PDF/report export
└── screens/
    ├── operator_qna_interactive.py  # Main Q&A interface
    ├── operations_dashboard.py      # KPI dashboard
    ├── qna_filters.py               # Checklist generation
    ├── answer_citations.py          # Step-by-step guides
    └── ticket_insights.py           # Ticket analysis

packages/
├── core_rag/
│   ├── llm_client.py                # Ollama integration
│   ├── retriever.py                 # Enhanced RAG retrieval
│   ├── rerank.py                    # CrossEncoder reranking
│   ├── embedding.py                 # SentenceTransformers
│   └── chroma_client.py             # Vector DB client
└── core_ingest/
    ├── pipeline.py                  # Ingestion with metadata
    └── loaders.py                   # PDF/document loaders
```

### Adding a New Screen

```python
# 1. Create screen file
# apps/shopfloor_copilot/screens/my_screen.py

from nicegui import ui

def build_my_screen():
    with ui.card().classes('sf-card'):
        ui.label('My Custom Screen')
        # Your UI code here

# 2. Import and add to ui.py
from apps.shopfloor_copilot.screens.my_screen import build_my_screen

# Add tab
tab_my_screen = ui.tab('My Screen', icon='widgets')

# Add panel
with ui.tab_panel(tab_my_screen).classes('p-4'):
    build_my_screen()
```

## Troubleshooting

### Ollama Connection Issues

**Problem**: `Error connecting to Ollama`

**Solutions**:
1. Ensure Ollama is running: `ollama serve`
2. Check model is available: `ollama list`
3. Pull model if needed: `ollama pull llama3.2`
4. For Docker: Use `OLLAMA_BASE_URL=http://host.docker.internal:11434`

### No Results from Retrieval

**Problem**: Empty results or "No relevant context"

**Solutions**:
1. Ingest some documents first via `/api/ingest`
2. Check ChromaDB is running: `docker ps | grep chroma`
3. Verify metadata filters match ingested documents
4. Try broader filters or no filters initially

### UI Not Loading

**Problem**: Blank page or 404 errors

**Solutions**:
1. Check port 8010 is not in use: `netstat -an | findstr 8010`
2. Verify all dependencies installed: `pip install -r requirements.txt`
3. Check logs: `docker compose logs shopfloor`

## Roadmap

### Phase 1 (✅ Complete)
- Ollama LLM integration
- MES context-aware retrieval
- Interactive operator Q&A
- Enhanced metadata ingestion

### Phase 2 (Next 2 weeks)
- KPI dashboard with charts
- SQL KPI tool (read-only MES queries)
- Hybrid retrieval (BM25 + vector)
- Guided checklist generation

### Phase 3 (Weeks 5-8)
- Real MES connector (Opcenter)
- Ticket similarity & root-cause
- Proactive alerts & recommendations
- Multi-language support

### Phase 4 (Weeks 9-12)
- Custom LLM fine-tuning
- Advanced analytics (predictive)
- Mobile interface
- Pilot deployment (Line A01)

## Contributing

This is an internal project for manufacturing AI integration. For questions or feature requests, contact the development team.

## License

Proprietary - Internal use only
