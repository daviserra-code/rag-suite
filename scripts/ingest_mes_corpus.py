#!/usr/bin/env python3
"""
MES Corpus Ingestion Script
Sprint 5 - Citation Discipline & Profile-Aware Knowledge Retrieval

Ingests generated MES documents into Chroma with full metadata:
- profile (aerospace_defence, pharma_process, automotive_discrete)
- doc_type (work_instruction, sop, deviation, calibration, etc.)
- station/operation (if applicable)
- document ID for citation tracking

Ensures:
- Single vector store for all profiles
- Metadata-based filtering
- Citation-ready document references
"""

import os
import json
from pathlib import Path
from packages.core_ingest.pipeline import ingest_file
from packages.core_rag.chroma_client import get_collection

# Source directory
MES_CORPUS_DIR = Path("data/documents/mes_corpus")

def parse_document_metadata(filepath: Path):
    """Extract metadata from document content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    metadata = {}
    
    # Parse header section
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('DOCUMENT ID:'):
            metadata['doc_id'] = line.split(':', 1)[1].strip()
        elif line.startswith('REVISION:') and i < 10:  # Header revision
            metadata['revision'] = line.split(':', 1)[1].strip()
        elif line.startswith('**Document Type:**'):
            metadata['doc_type'] = line.split('**Document Type:**', 1)[1].strip()
        elif line.startswith('**Profile:**'):
            metadata['profile'] = line.split('**Profile:**', 1)[1].strip()
        elif line.startswith('**Station/Operation:**'):
            metadata['station'] = line.split('**Station/Operation:**', 1)[1].strip()
        elif line.startswith('# '):
            metadata['title'] = line[2:].strip()
            break
    
    return metadata

def ingest_mes_corpus():
    """Ingest all MES corpus documents with metadata."""
    print("=" * 80)
    print("MES CORPUS INGESTION - Sprint 5")
    print("=" * 80)
    print()
    
    if not MES_CORPUS_DIR.exists():
        print(f"❌ Error: MES corpus directory not found: {MES_CORPUS_DIR}")
        print("Run generate_mes_documents.py first!")
        return
    
    # Load manifest
    manifest_path = MES_CORPUS_DIR / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        print(f"✓ Loaded manifest: {len(manifest['documents'])} documents")
        print(f"  Profiles: {', '.join(manifest['profiles'])}")
        print()
    else:
        print("⚠️  No manifest found - proceeding with file scan")
        manifest = None
    
    # Track ingestion statistics
    stats = {
        "total": 0,
        "success": 0,
        "errors": 0,
        "by_profile": {},
        "by_doc_type": {}
    }
    
    # Process each profile directory
    for profile_dir in sorted(MES_CORPUS_DIR.iterdir()):
        if not profile_dir.is_dir():
            continue
        
        profile_name = profile_dir.name
        print(f"\n{'=' * 80}")
        print(f"Processing Profile: {profile_name.upper()}")
        print(f"{'=' * 80}\n")
        
        if profile_name not in stats["by_profile"]:
            stats["by_profile"][profile_name] = 0
        
        # Process each document in profile
        for doc_file in sorted(profile_dir.glob("*.md")):
            stats["total"] += 1
            
            try:
                # Parse document metadata
                doc_meta = parse_document_metadata(doc_file)
                doc_id = doc_meta.get('doc_id', doc_file.stem)
                doc_type = doc_meta.get('doc_type', 'unknown')
                doc_title = doc_meta.get('title', doc_file.stem)
                station = doc_meta.get('station')
                
                # Track by doc_type
                if doc_type not in stats["by_doc_type"]:
                    stats["by_doc_type"][doc_type] = 0
                stats["by_doc_type"][doc_type] += 1
                
                print(f"📄 Ingesting: {doc_id}")
                print(f"   Title: {doc_title}")
                print(f"   Type: {doc_type}")
                print(f"   Profile: {profile_name}")
                if station:
                    print(f"   Station: {station}")
                
                # Read document content
                with open(doc_file, 'rb') as f:
                    content = f.read()
                
                # Ingest with full metadata
                result = ingest_file(
                    app="shopfloor_docs",
                    doctype=doc_type,  # doc_type becomes doctype in Chroma
                    filename=str(doc_file.name),
                    content=content,
                    station=station,
                    rev=doc_meta.get('revision')
                )
                
                # Add profile to metadata manually (extend base_meta)
                # We need to update the ingestion to include profile
                # For now, we'll do a second pass to add profile metadata
                coll = get_collection()
                
                # Get the chunks that were just added
                chunk_ids = [f"{result['doc_id']}-{i}" for i in range(result['chunks'])]
                
                # Update metadata to include profile and full doc_id
                for chunk_id in chunk_ids:
                    try:
                        # Get existing metadata
                        existing = coll.get(ids=[chunk_id])
                        if existing and existing['metadatas']:
                            meta = existing['metadatas'][0]
                            # Add profile and original doc_id
                            meta['profile'] = profile_name
                            meta['original_doc_id'] = doc_id
                            meta['doc_title'] = doc_title
                            # Update with enhanced metadata
                            coll.update(
                                ids=[chunk_id],
                                metadatas=[meta]
                            )
                    except Exception as e:
                        print(f"   ⚠️  Could not update metadata for chunk {chunk_id}: {e}")
                
                print(f"   ✅ Success: {result['chunks']} chunks ingested")
                print(f"      Doc ID: {result['doc_id']}")
                print()
                
                stats["success"] += 1
                stats["by_profile"][profile_name] += 1
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                print()
                stats["errors"] += 1
    
    # Print summary
    print("\n" + "=" * 80)
    print("INGESTION SUMMARY")
    print("=" * 80)
    print()
    print(f"Total documents processed: {stats['total']}")
    print(f"✅ Successfully ingested: {stats['success']}")
    print(f"❌ Errors: {stats['errors']}")
    print()
    
    print("By Profile:")
    for profile, count in sorted(stats["by_profile"].items()):
        print(f"  {profile:30} {count:3} documents")
    print()
    
    print("By Document Type:")
    for doc_type, count in sorted(stats["by_doc_type"].items()):
        print(f"  {doc_type:30} {count:3} documents")
    print()
    
    # Verify collection count
    try:
        coll = get_collection()
        total_chunks = coll.count()
        print(f"📚 Total chunks in Chroma collection: {total_chunks}")
        print()
        
        # Sample a few documents to verify metadata
        print("Sample Document Metadata (first 3 chunks):")
        sample = coll.get(limit=3)
        if sample and sample['metadatas']:
            for i, meta in enumerate(sample['metadatas'][:3], 1):
                print(f"\n{i}. Chunk ID: {sample['ids'][i-1]}")
                print(f"   Profile: {meta.get('profile', 'N/A')}")
                print(f"   Doc Type: {meta.get('doctype', 'N/A')}")
                print(f"   Doc ID: {meta.get('original_doc_id', meta.get('doc_id', 'N/A'))}")
                print(f"   Title: {meta.get('doc_title', 'N/A')}")
                print(f"   Station: {meta.get('station', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Could not verify collection: {e}")
    
    print("\n" + "=" * 80)
    print("Next Steps:")
    print("1. Test profile-aware retrieval with different queries")
    print("2. Verify citation discipline in diagnostics responses")
    print("3. Compare explanations across profiles")
    print("=" * 80)

if __name__ == "__main__":
    ingest_mes_corpus()
