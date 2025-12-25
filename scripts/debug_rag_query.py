#!/usr/bin/env python3
"""Debug RAG retrieval for Sprint 5 citation test"""

from packages.core_rag.chroma_client import get_collection
from packages.diagnostics.explainer import DiagnosticsExplainer

# Test query as explainer would do it
collection = get_collection()

# Test 1: Query without any filters
print("TEST 1: Query without filters")
print("Query: 'ST22 hydraulic press'")
results1 = collection.query(
    query_texts=["ST22 hydraulic press"],
    n_results=5
)
print(f"Results: {len(results1['ids'][0])}")
if results1['ids'][0]:
    print("Top results:")
    for i, (doc_id, meta, dist) in enumerate(zip(results1['ids'][0][:3], results1['metadatas'][0][:3], results1['distances'][0][:3])):
        print(f"  {i+1}. {meta.get('original_doc_id', 'NO_ID')} - dist: {dist:.3f} - {meta.get('doc_title', '')[:50]}")

# Test 2: Query with aerospace profile filter
print("\nTEST 2: Query with aerospace_defence profile filter")
print("Query: 'ST22 hydraulic press'")
results2 = collection.query(
    query_texts=["ST22 hydraulic press"],
    n_results=5,
    where={"profile": "aerospace_defence"}
)
print(f"Results: {len(results2['ids'][0])}")
if results2['ids'][0]:
    print("Top results:")
    for i, (doc_id, meta, dist) in enumerate(zip(results2['ids'][0][:3], results2['metadatas'][0][:3], results2['distances'][0][:3])):
        print(f"  {i+1}. {meta.get('original_doc_id', 'NO_ID')} - dist: {dist:.3f} - {meta.get('doc_title', '')[:50]}")

# Test 3: Get all aerospace docs to see what we have
print("\nTEST 3: All aerospace_defence documents")
aero_docs = collection.get(
    where={"profile": "aerospace_defence"},
    limit=100,
    include=["metadatas"]
)
print(f"Total aerospace documents: {len(aero_docs['ids'])}")
print("Document IDs:")
for i, meta in enumerate(aero_docs['metadatas'][:10]):
    print(f"  {i+1}. {meta.get('original_doc_id', 'NO_ID')} - {meta.get('doc_title', '')[:60]}")

# Test 4: Query for calibration
print("\nTEST 4: Query for 'calibration torque wrench'")
results4 = collection.query(
    query_texts=["calibration torque wrench"],
    n_results=5,
    where={"profile": "aerospace_defence"}
)
print(f"Results: {len(results4['ids'][0])}")
if results4['ids'][0]:
    print("Top results:")
    for i, (doc_id, meta, dist) in enumerate(zip(results4['ids'][0][:3], results4['metadatas'][0][:3], results4['distances'][0][:3])):
        print(f"  {i+1}. {meta.get('original_doc_id', 'NO_ID')} - dist: {dist:.3f}")
