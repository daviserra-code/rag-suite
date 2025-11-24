import uuid
from typing import Dict, Any, Optional
from packages.core_ingest.loaders import load_document
from packages.core_rag.chroma_client import get_collection
from packages.core_rag.embedding import embed_texts

def ingest_file(
    app: str, 
    doctype: str, 
    filename: str, 
    content: bytes,
    # MES Context metadata
    plant: Optional[str] = None,
    line: Optional[str] = None,
    station: Optional[str] = None,
    turno: Optional[str] = None,
    rev: Optional[str] = None,
    valid_from: Optional[str] = None,
    valid_to: Optional[str] = None,
    safety_tag: Optional[str] = None,
    lang: Optional[str] = "en"
) -> Dict[str, Any]:
    """
    Ingest a document with enhanced MES context metadata.
    
    Args:
        app: Application name
        doctype: Document type (WI, SOP, EWI, manual, etc.)
        filename: Original filename
        content: File content bytes
        plant: Plant identifier (e.g., "P01")
        line: Production line (e.g., "A01")
        station: Work station (e.g., "S110")
        turno: Shift identifier (e.g., "T1", "T2", "T3")
        rev: Document revision (e.g., "v1.2")
        valid_from: Document validity start date (ISO format)
        valid_to: Document validity end date (ISO format)
        safety_tag: Safety classification (e.g., "critical", "standard")
        lang: Language code (e.g., "en", "it", "de")
    """
    doc_id = f"{doctype}-{uuid.uuid4().hex[:8]}"
    chunks = load_document(content, filename)
    coll = get_collection()
    if not chunks:
        return {"doc_id": doc_id, "chunks": 0}

    ids = [f"{doc_id}-{i}" for i,_ in enumerate(chunks)]
    documents = [c["text"] for c in chunks]

    # Build metadata with MES context
    base_meta = {
        "app": app,
        "doctype": doctype,
        "doc_id": doc_id,
        "source_url": filename,
        "lang": lang or "en"
    }
    
    # Add optional MES context fields
    if plant:
        base_meta["plant"] = plant
    if line:
        base_meta["line"] = line
    if station:
        base_meta["station"] = station
    if turno:
        base_meta["turno"] = turno
    if rev:
        base_meta["rev"] = rev
    if valid_from:
        base_meta["valid_from"] = valid_from
    if valid_to:
        base_meta["valid_to"] = valid_to
    if safety_tag:
        base_meta["safety_tag"] = safety_tag

    metadatas = []
    for c in chunks:
        meta = base_meta.copy()
        meta["page_from"] = c["page_from"]
        meta["page_to"] = c["page_to"]
        metadatas.append(meta)

    embeddings = embed_texts(documents)
    coll.add(ids=ids, metadatas=metadatas, documents=documents, embeddings=embeddings)
    
    return {
        "doc_id": doc_id, 
        "chunks": len(chunks),
        "metadata": base_meta
    }
