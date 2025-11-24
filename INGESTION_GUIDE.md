# Document Ingestion Guide - Shopfloor Copilot

## Supported File Formats

- **PDF** (.pdf): Work instructions, manuals, procedures
- **Markdown** (.md): Technical documentation with section awareness
- **Text** (.txt): Plain text documents, notes, checklists

## File Format Features

### PDF Files
- Extracts text with page numbers
- Preserves multi-page context
- Best for: Official documents, scanned procedures

### Markdown Files
- Section-aware chunking (respects `#` headers)
- Preserves document structure
- Best for: Technical docs, SOPs with headings

### Text Files
- Simple line-based chunking
- UTF-8 encoding support
- Best for: Notes, checklists, quick references

## Ingestion Methods

### Method 1: API Endpoint

**Endpoint:** `POST http://localhost:8010/api/ingest`

**Required Fields:**
- `app`: Application name (e.g., "shopfloor")
- `doctype`: Document type (e.g., "SOP", "WI", "EWI", "safety", "QA")
- `file`: File upload (multipart/form-data)

**Optional MES Context:**
- `plant`: Plant ID (e.g., "P01")
- `line`: Production line (e.g., "A01")
- `station`: Work station (e.g., "S110")
- `turno`: Shift (e.g., "T1", "T2", "T3")
- `rev`: Document revision (e.g., "v1.2")
- `valid_from`: Start date (ISO format: "2024-01-01")
- `valid_to`: End date (ISO format: "2025-12-31")
- `safety_tag`: Safety level ("critical", "standard")
- `lang`: Language code ("en", "it", "de")

**Example with curl:**
```bash
curl -X POST http://localhost:8010/api/ingest \
  -F "app=shopfloor" \
  -F "doctype=SOP" \
  -F "plant=P01" \
  -F "line=A01" \
  -F "station=S110" \
  -F "lang=en" \
  -F "file=@assembly_procedure.pdf"
```

**Example with Python:**
```python
import requests

url = "http://localhost:8010/api/ingest"
files = {"file": open("assembly_procedure.pdf", "rb")}
data = {
    "app": "shopfloor",
    "doctype": "SOP",
    "plant": "P01",
    "line": "A01",
    "station": "S110",
    "lang": "en"
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### Method 2: Bulk Ingestion Script

**Command:**
```bash
python bulk_ingest.py --folder ./data/documents
```

**Folder Structure Example:**
```
documents/
├── SOPs/
│   ├── P01_A01_S110_T1_assembly.pdf
│   ├── P01_A01_S110_quality_check.md
│   └── general_procedures.txt
├── safety/
│   ├── lockout_tagout.pdf
│   └── emergency_procedures.md
├── quality/
│   ├── inspection_checklist.md
│   └── defect_codes.txt
└── training/
    ├── onboarding_guide.pdf
    └── operator_manual.md
```

**Filename Convention for Auto-Metadata:**
Format: `[PLANT]_[LINE]_[STATION]_[TURNO]_description.ext`

Examples:
- `P01_A01_S110_T1_assembly.pdf` → plant=P01, line=A01, station=S110, turno=T1
- `P02_B01_quality_check.md` → plant=P02, line=B01
- `safety_procedures.txt` → no MES context (general document)

**Document Type Auto-Detection:**
Folder name determines doctype:
- `SOPs/` → doctype="SOP"
- `safety/` → doctype="safety", safety_tag="critical"
- `quality/` → doctype="QA"
- `manuals/` → doctype="manual"
- `training/` → doctype="training"
- `EWI/` → doctype="EWI" (Electronic Work Instruction)
- `WI/` → doctype="WI" (Work Instruction)

## MES Context Metadata

### Plant Hierarchy
```
Plant (P01)
└── Line (A01)
    └── Station (S110)
        └── Shift (T1, T2, T3)
```

### Document Types (doctype)
- **SOP**: Standard Operating Procedure
- **WI**: Work Instruction
- **EWI**: Electronic Work Instruction
- **safety**: Safety procedures (lockout/tagout, PPE, emergency)
- **QA**: Quality assurance documents
- **manual**: Equipment manuals, technical references
- **training**: Training materials, onboarding guides

### Safety Tags
- **critical**: Safety-critical documents (lockout/tagout, emergency procedures)
- **standard**: Regular operational documents

### Language Codes
- **en**: English
- **it**: Italian
- **de**: German
- **es**: Spanish
- **fr**: French

## Usage Examples

### Example 1: Ingest Station-Specific SOP
```bash
curl -X POST http://localhost:8010/api/ingest \
  -F "app=shopfloor" \
  -F "doctype=SOP" \
  -F "plant=P01" \
  -F "line=A01" \
  -F "station=S110" \
  -F "turno=T1" \
  -F "rev=v2.1" \
  -F "lang=en" \
  -F "file=@S110_assembly_procedure.pdf"
```

### Example 2: Ingest Safety Document (Critical)
```bash
curl -X POST http://localhost:8010/api/ingest \
  -F "app=shopfloor" \
  -F "doctype=safety" \
  -F "plant=P01" \
  -F "safety_tag=critical" \
  -F "lang=en" \
  -F "file=@lockout_tagout_procedure.md"
```

### Example 3: Ingest Training Material (No MES Context)
```bash
curl -X POST http://localhost:8010/api/ingest \
  -F "app=shopfloor" \
  -F "doctype=training" \
  -F "lang=it" \
  -F "file=@operator_onboarding_guide.txt"
```

### Example 4: Bulk Ingest with Auto-Metadata
```bash
# Organize documents in folders
mkdir -p data/documents/SOPs
mkdir -p data/documents/safety
mkdir -p data/documents/quality

# Copy files with naming convention
# P01_A01_S110_assembly.pdf
# P01_A01_S110_quality_check.md
# safety_lockout_tagout.txt

# Run bulk ingestion
python bulk_ingest.py --folder ./data/documents
```

## Retrieval and Querying

Once documents are ingested, they're available for:

1. **Hybrid Retrieval**: BM25 keyword + vector semantic search
2. **Filtered Search**: Filter by plant, line, station, shift, doctype, safety_tag
3. **Multi-Language**: Query in any language, retrieves matching language docs

**Example Query:**
```bash
curl -X POST http://localhost:8010/api/ask/llm \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the assembly steps for S110?",
    "filters": {
      "station": "S110",
      "doctype": "SOP"
    }
  }'
```

## Checking Ingestion Status

**API Health Check:**
```bash
curl http://localhost:8010/health
```

**Check Collection Size:**
```python
from packages.core_rag.chroma_client import get_collection

coll = get_collection()
print(f"Total documents: {coll.count()}")
```

## Best Practices

1. **Use Naming Conventions**: Include MES context in filenames for auto-metadata
2. **Organize by Type**: Use folder structure for automatic doctype assignment
3. **Version Control**: Use `rev` field for document versions
4. **Safety Critical**: Always tag safety documents with `safety_tag=critical`
5. **Language Tagging**: Specify `lang` for multi-language support
6. **Validity Dates**: Use `valid_from`/`valid_to` for time-sensitive procedures

## Troubleshooting

**Issue: 0 results after ingestion**
- Check collection: `coll.count()`
- Verify API response: Check `chunks` count in response
- Restart container: `docker compose restart shopfloor`

**Issue: Unsupported file format**
- Supported: .pdf, .md, .txt
- Convert other formats to PDF or Markdown first

**Issue: Encoding errors with .txt files**
- Ensure UTF-8 encoding
- Use `notepad++ → Encoding → UTF-8` for Windows files

**Issue: Metadata not applied**
- Check filename convention: `[PLANT]_[LINE]_[STATION]_[TURNO]_name.ext`
- Verify folder name matches DOCTYPE_CONFIG in bulk_ingest.py
- Manually specify metadata in API call if auto-detection fails
