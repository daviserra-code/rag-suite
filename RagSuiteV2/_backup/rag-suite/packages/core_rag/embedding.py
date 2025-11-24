import os
from sentence_transformers import SentenceTransformer

_model = None

def get_embedder():
    global _model
    if _model is None:
        name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        _model = SentenceTransformer(name)
    return _model

def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    return model.encode(texts, normalize_embeddings=True).tolist()

def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
