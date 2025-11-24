from typing import Dict, Any, List
from packages.core_rag.chroma_client import get_collection
from packages.core_rag.embedding import embed_query
from packages.core_rag.rerank import rerank

def retrieve_and_answer(app: str, query: str, filters: Dict[str, Any]) -> Dict[str, Any]:
    coll = get_collection()
    where = {"app": app}
    for k, v in (filters or {}).items():
        if v is not None and v != "":
            where[k] = v

    q_emb = embed_query(query)
    res = coll.query(query_embeddings=[q_emb], n_results=15, where=where)

    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]

    passages = [{"text": d, "meta": m} for d, m in zip(docs, metas)]
    top = rerank(query, passages, top_k=5)

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

    return {"answer": answer_text, "citations": citations, "filters_applied": where, "hits": len(docs)}
