import os, chromadb

def get_collection(name: str | None = None):
    client = chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", "8000")),
    )
    coll = client.get_or_create_collection(name or os.getenv("CHROMA_COLLECTION", "rag_core"),
                                           metadata={"hnsw:space":"cosine"})
    return coll
