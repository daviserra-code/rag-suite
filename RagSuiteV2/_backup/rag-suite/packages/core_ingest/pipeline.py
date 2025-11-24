import uuid
from typing import Dict, Any
from packages.core_ingest.loaders import pdf_to_chunks
from packages.core_rag.chroma_client import get_collection
from packages.core_rag.embedding import embed_texts

def ingest_file(app: str, doctype: str, filename: str, content: bytes) -> Dict[str, Any]:
    doc_id = f"{doctype}-{uuid.uuid4().hex[:8]}"
    chunks = pdf_to_chunks(content)
    coll = get_collection()
    if not chunks:
        return {"doc_id": doc_id, "chunks": 0}

    ids = [f"{doc_id}-{i}" for i,_ in enumerate(chunks)]
    documents = [c["text"] for c in chunks]

    metadatas = [{
        "app": app,
        "doctype": doctype,
        "doc_id": doc_id,
        "source_url": filename,
        "page_from": c["page_from"],
        "page_to": c["page_to"]
    } for c in chunks]

    embeddings = embed_texts(documents)
    coll.add(ids=ids, metadatas=metadatas, documents=documents, embeddings=embeddings)
    return {"doc_id": doc_id, "chunks": len(chunks)}
