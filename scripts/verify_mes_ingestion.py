#!/usr/bin/env python3
"""Verify MES corpus ingestion and metadata."""

from packages.core_rag.chroma_client import get_collection
import json

def verify_ingestion():
    coll = get_collection()
    
    print("=" * 80)
    print("CHROMA COLLECTION VERIFICATION")
    print("=" * 80)
    print()
    
    total = coll.count()
    print(f"Total chunks in collection: {total}")
    print()
    
    # Get sample documents
    sample = coll.get(limit=10)
    
    print("Sample Documents (first 10 chunks):")
    print("-" * 80)
    
    for i, (chunk_id, meta) in enumerate(zip(sample['ids'], sample['metadatas']), 1):
        print(f"\n{i}. Chunk ID: {chunk_id}")
        print(f"   Profile: {meta.get('profile', 'N/A')}")
        print(f"   Doc Type: {meta.get('doctype', 'N/A')}")
        print(f"   Doc ID: {meta.get('original_doc_id', meta.get('doc_id', 'N/A'))}")
        print(f"   Title: {meta.get('doc_title', 'N/A')}")
        print(f"   Station: {meta.get('station', 'N/A')}")
    
    print()
    print("=" * 80)
    
    # Check profile distribution
    profiles = {}
    doc_types = {}
    
    all_data = coll.get(limit=total if total < 1000 else 1000)
    for meta in all_data['metadatas']:
        profile = meta.get('profile', 'unknown')
        doc_type = meta.get('doctype', 'unknown')
        
        profiles[profile] = profiles.get(profile, 0) + 1
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
    
    print("\nProfile Distribution:")
    for profile, count in sorted(profiles.items()):
        print(f"  {profile:30} {count:4} chunks")
    
    print("\nDoc Type Distribution:")
    for doc_type, count in sorted(doc_types.items()):
        print(f"  {doc_type:30} {count:4} chunks")
    
    print()

if __name__ == "__main__":
    verify_ingestion()
