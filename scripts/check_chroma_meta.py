#!/usr/bin/env python3
"""Check Chroma metadata for MES corpus documents"""

from packages.core_rag.chroma_client import get_collection
import json

coll = get_collection()
print(f"\nTotal documents in collection: {coll.count()}")

# Get a sample with metadata
results = coll.get(limit=10, include=["metadatas", "documents"])

print("\nSample metadata (first 5):")
for i, meta in enumerate(results['metadatas'][:5]):
    print(f"\n{i+1}. {meta.get('original_doc_id', 'NO_ID')}")
    print(f"   Profile: {meta.get('profile', 'NO_PROFILE')}")
    print(f"   Doc Type: {meta.get('doctype', 'NO_DOCTYPE')}")
    print(f"   App: {meta.get('app', 'NO_APP')}")
    print(f"   Title: {meta.get('doc_title', 'NO_TITLE')[:60]}...")

# Check profile distribution
profiles = {}
for meta in results['metadatas']:
    p = meta.get('profile', 'unknown')
    profiles[p] = profiles.get(p, 0) + 1

print(f"\nProfile distribution (first 10 docs):")
for profile, count in sorted(profiles.items()):
    print(f"  {profile}: {count}")

# Check if we have any aerospace_defence docs
aero_results = coll.get(where={"profile": "aerospace_defence"}, limit=3, include=["metadatas"])
print(f"\nAerospace & Defence docs: {len(aero_results['ids'])}")
if aero_results['ids']:
    for i, meta in enumerate(aero_results['metadatas'][:3]):
        print(f"  {i+1}. {meta.get('original_doc_id')} - {meta.get('doc_title', '')[:50]}")
