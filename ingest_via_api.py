"""
Simple Python script to ingest documents via HTTP API
Run: python ingest_via_api.py
"""

import requests
from pathlib import Path

API_URL = "http://localhost:8000/ingest"
DOCS_PATH = Path("data/documents")
APP_NAME = "shopfloor_docs"

def ingest_file(filepath: Path, doctype: str):
    """Upload a single file to the ingest API"""
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (filepath.name, f, 'application/octet-stream')}
            data = {
                'app': APP_NAME,
                'doctype': doctype
            }
            
            response = requests.post(API_URL, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ {filepath.name} - {result.get('stats', {})}")
                return True
            else:
                print(f"  ❌ {filepath.name} - Status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"  ❌ {filepath.name} - Error: {e}")
        return False

def main():
    ingested = 0
    errors = 0
    
    print("📚 Starting document ingestion...\n")
    
    # Ingest SOPs
    print("📄 Ingesting SOPs (procedures)...")
    sops_path = DOCS_PATH / "SOPs"
    if sops_path.exists():
        for file in sops_path.glob("*.md"):
            if ingest_file(file, "procedure"):
                ingested += 1
            else:
                errors += 1
    
    # Ingest Safety docs
    print("\n🛡️  Ingesting Safety documents...")
    safety_path = DOCS_PATH / "safety"
    if safety_path.exists():
        for file in safety_path.rglob("*.md"):
            if ingest_file(file, "safety"):
                ingested += 1
            else:
                errors += 1
        for file in safety_path.rglob("*.txt"):
            if ingest_file(file, "safety"):
                ingested += 1
            else:
                errors += 1
    
    # Ingest Quality docs
    print("\n✅ Ingesting Quality documents...")
    quality_path = DOCS_PATH / "quality"
    if quality_path.exists():
        for file in quality_path.glob("*.md"):
            if ingest_file(file, "quality"):
                ingested += 1
            else:
                errors += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Ingestion Summary:")
    print(f"   ✅ Successfully ingested: {ingested} documents")
    print(f"   ❌ Errors: {errors} documents")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
