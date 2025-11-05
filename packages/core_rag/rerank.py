import os
from sentence_transformers import CrossEncoder

_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        name = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-12-v2")
        _reranker = CrossEncoder(name)
    return _reranker

def rerank(query: str, passages: list[dict], top_k: int = 5) -> list[dict]:
    if not passages:
        return []
    model = get_reranker()
    pairs = [(query, p["text"]) for p in passages]
    scores = model.predict(pairs).tolist()
    for p, s in zip(passages, scores):
        p["score"] = float(s)
    passages.sort(key=lambda x: x["score"], reverse=True)
    return passages[:top_k]
