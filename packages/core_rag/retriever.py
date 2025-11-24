import os
from typing import Dict, Any, List, Optional
from packages.core_rag.chroma_client import get_collection
from packages.core_rag.embedding import embed_query
from packages.core_rag.rerank import rerank

def build_mes_filters(app: str, filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build ChromaDB where clause with MES context filters.
    Supports: plant, line, station, turno, doctype, safety_tag, lang
    """
    where = {"app": app}
    
    # Standard MES context filters
    mes_fields = ["plant", "line", "station", "turno", "doctype", "safety_tag", "lang"]
    for field in mes_fields:
        value = filters.get(field)
        if value is not None and value != "":
            where[field] = value
    
    # Legacy support for any other filters
    for k, v in filters.items():
        if k not in mes_fields and v is not None and v != "":
            where[k] = v
    
    return where


def retrieve_passages(
    app: str, 
    query: str, 
    filters: Optional[Dict[str, Any]] = None,
    n_results: int = 15,
    rerank_top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve and rerank passages based on query and filters.
    
    Args:
        app: Application name (e.g., "shopfloor_copilot")
        query: User's search query
        filters: Optional MES context filters (plant, line, station, turno, etc.)
        n_results: Number of results to retrieve from vector search
        rerank_top_k: Number of top results after reranking
        
    Returns:
        List of passages with text, metadata, and rerank scores
    """
    coll = get_collection()
    where = build_mes_filters(app, filters or {})

    q_emb = embed_query(query)
    res = coll.query(query_embeddings=[q_emb], n_results=n_results, where=where)

    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]

    passages = [{"text": d, "meta": m} for d, m in zip(docs, metas)]
    
    # Rerank if enabled
    enable_rerank = os.getenv("ENABLE_RERANK", "true").lower() == "true"
    if enable_rerank and passages:
        top = rerank(query, passages, top_k=rerank_top_k)
    else:
        top = passages[:rerank_top_k]
    
    return top


def retrieve_and_answer(app: str, query: str, filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy method - retrieve passages and create simple answer from top results.
    Kept for backward compatibility with existing code.
    """
    top = retrieve_passages(app, query, filters)

    def first_sentences(t: str, n: int = 2) -> str:
        parts = [p.strip() for p in t.split(".") if p.strip()]
        return ". ".join(parts[:n]) + ("." if parts else "")

    summary_parts: List[str] = [first_sentences(p["text"], 2) for p in top[:3]]
    answer_text = "\n\n".join(summary_parts) if summary_parts else "Nessun risultato ad alta confidenza."

    citations = []
    for p in top[:4]:
        m = p["meta"]
        citations.append({
            "doc_id": m.get("doc_id", "?"),
            "pages": f"{m.get('page_from','?')}-{m.get('page_to','?')}",
            "url": m.get("source_url", ""),
            "score": round(p.get("score", 0.0), 3)
        })

    where = build_mes_filters(app, filters or {})
    return {"answer": answer_text, "citations": citations, "filters_applied": where, "hits": len(top)}
