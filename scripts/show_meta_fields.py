from packages.core_rag.chroma_client import get_collection
import json

coll = get_collection()
r = coll.get(limit=3, where={"profile": "aerospace_defence"}, include=["metadatas"])
print("Aerospace Defence metadata fields:")
for i, meta in enumerate(r['metadatas'][:1]):
    print(json.dumps(meta, indent=2))
