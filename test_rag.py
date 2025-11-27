from packages.core_rag.retriever import retrieve_passages, retrieve_and_answer

# Test 1: Direct retrieval
print("Test 1: Direct retrieval")
results = retrieve_passages('shopfloor_docs', 'emergency stop procedures', {}, n_results=5)
print(f'Found {len(results)} results')
for r in results[:3]:
    print(f'  - Score: {r.get("score", 0):.3f}, Text: {r["text"][:80]}...')

# Test 2: Retrieve and answer
print("\nTest 2: Retrieve and answer")
answer = retrieve_and_answer('shopfloor_docs', 'emergency stop procedures', {})
print(f'Answer: {answer["answer"][:200]}...')
print(f'Citations: {len(answer["citations"])} found')
print(f'Hits: {answer["hits"]}')

# Test 3: Check what apps exist in collection
print("\nTest 3: Check collection metadata")
from packages.core_rag.chroma_client import get_collection
coll = get_collection()
sample = coll.get(limit=5, include=['metadatas'])
print(f'Sample apps in collection:')
for meta in sample['metadatas']:
    print(f'  - app: {meta.get("app")}, doctype: {meta.get("doctype")}')
