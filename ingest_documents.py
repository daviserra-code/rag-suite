"""
Quick script to ingest all documents from data/documents into ChromaDB
Run from inside the API container: docker exec rag-suite-api-1 python ingest_documents.py
"""

import os
from pathlib import Path
from packages.core_ingest.pipeline import ingest_file

def ingest_directory(base_path: str, app: str = "shopfloor_docs"):
    """Recursively ingest all documents from a directory"""
    
    base = Path(base_path)
    if not base.exists():
        print(f"❌ Directory not found: {base_path}")
        return
    
    # Define document type mappings
    doctype_map = {
        'SOPs': 'procedure',
        'safety': 'safety',
        'quality': 'quality',
    }
    
    ingested_count = 0
    error_count = 0
    
    print(f"📚 Starting document ingestion from {base_path}")
    print(f"🎯 Target app: {app}\n")
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(base):
        for filename in files:
            # Skip non-document files
            if not (filename.endswith('.md') or filename.endswith('.txt') or filename.endswith('.pdf')):
                continue
            
            filepath = Path(root) / filename
            relative_path = filepath.relative_to(base)
            
            # Determine doctype from folder structure
            doctype = 'general'
            for folder, dtype in doctype_map.items():
                if folder in str(relative_path):
                    doctype = dtype
                    break
            
            try:
                print(f"📄 Ingesting: {relative_path} (type: {doctype})")
                
                # Read file content
                with open(filepath, 'rb') as f:
                    content = f.read()
                
                # Ingest the file
                stats = ingest_file(
                    app=app,
                    doctype=doctype,
                    filename=str(relative_path),
                    content=content
                )
                
                print(f"   ✅ Success: {stats}")
                ingested_count += 1
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                error_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Ingestion Summary:")
    print(f"   ✅ Successfully ingested: {ingested_count} documents")
    print(f"   ❌ Errors: {error_count} documents")
    print(f"{'='*60}\n")
    
    # Verify collection count
    try:
        from packages.core_rag.chroma_client import get_collection
        coll = get_collection()
        print(f"📚 Total documents in collection '{coll.name}': {coll.count()}")
    except Exception as e:
        print(f"❌ Could not verify collection: {e}")


if __name__ == "__main__":
    # Ingest documents from the mounted data directory
    data_path = "/app/data/documents"
    
    if os.path.exists(data_path):
        ingest_directory(data_path, app="shopfloor_docs")
    else:
        print(f"❌ Data directory not found: {data_path}")
        print("Make sure the container has the data volume mounted correctly.")
