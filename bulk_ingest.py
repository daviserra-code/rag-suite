"""
Bulk Document Ingestion Script for Shopfloor Copilot

This script ingests multiple documents from a folder structure with metadata.
Supports .pdf, .md, and .txt files.

Usage:
    python bulk_ingest.py --folder ./data/documents

Folder Structure Example:
    documents/
        SOPs/
            S110_assembly_procedure.pdf
            S110_assembly_procedure.md
        safety/
            lockout_tagout.txt
        quality/
            inspection_checklist.md

Metadata can be configured in the script or via naming conventions.
"""

import argparse
import os
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional

# API Configuration
API_BASE = "http://localhost:8010"
INGEST_ENDPOINT = f"{API_BASE}/api/ingest"

# Tracking file for ingested documents
TRACKING_FILE = ".ingested_files.json"

# Default metadata
DEFAULT_APP = "shopfloor"
DEFAULT_LANG = "en"

# Metadata mapping by document type (folder name)
DOCTYPE_CONFIG = {
    "SOPs": {
        "doctype": "SOP",
        "safety_tag": "standard"
    },
    "safety": {
        "doctype": "safety",
        "safety_tag": "critical"
    },
    "quality": {
        "doctype": "QA",
        "safety_tag": "standard"
    },
    "manuals": {
        "doctype": "manual",
        "safety_tag": "standard"
    },
    "training": {
        "doctype": "training",
        "safety_tag": "standard"
    },
    "EWI": {
        "doctype": "EWI",
        "safety_tag": "standard"
    },
    "WI": {
        "doctype": "WI",
        "safety_tag": "standard"
    }
}

# Parse MES context from filename
# Example: P01_A01_S110_T1_assembly.pdf -> plant=P01, line=A01, station=S110, turno=T1
def parse_filename_metadata(filename: str) -> Dict[str, str]:
    """
    Extract MES context from filename.
    
    Naming convention: [PLANT]_[LINE]_[STATION]_[TURNO]_description.ext
    Example: P01_A01_S110_T1_assembly_procedure.pdf
    """
    meta = {}
    parts = filename.split("_")
    
    if len(parts) >= 1 and parts[0].startswith("P"):
        meta["plant"] = parts[0]
    if len(parts) >= 2 and parts[1].startswith("A"):
        meta["line"] = parts[1]
    if len(parts) >= 3 and parts[2].startswith("S"):
        meta["station"] = parts[2]
    if len(parts) >= 4 and parts[3].startswith("T"):
        meta["turno"] = parts[3]
    
    return meta

def ingest_document(
    filepath: Path,
    doctype: str,
    app: str = DEFAULT_APP,
    lang: str = DEFAULT_LANG,
    **metadata
) -> Dict:
    """
    Ingest a single document via API.
    
    Args:
        filepath: Path to document
        doctype: Document type (SOP, WI, etc.)
        app: Application name
        lang: Language code
        **metadata: Additional MES context (plant, line, station, turno, etc.)
    """
    with open(filepath, "rb") as f:
        files = {"file": (filepath.name, f)}
        data = {
            "app": app,
            "doctype": doctype,
            "lang": lang,
            **metadata
        }
        
        response = requests.post(INGEST_ENDPOINT, files=files, data=data)
        response.raise_for_status()
        return response.json()

def bulk_ingest(folder: str, verbose: bool = True, skip_existing: bool = True) -> List[Dict]:
    """
    Ingest all supported documents from a folder structure.
    
    Args:
        folder: Root folder containing documents
        verbose: Print progress messages
        skip_existing: Skip files that were already ingested
    
    Returns:
        List of ingestion results
    """
    folder_path = Path(folder)
    if not folder_path.exists():
        raise ValueError(f"Folder not found: {folder}")
    
    # Load tracking file
    tracking_path = folder_path / TRACKING_FILE
    ingested_files = {}
    if skip_existing and tracking_path.exists():
        with open(tracking_path, 'r') as f:
            ingested_files = json.load(f)
    
    results = []
    supported_extensions = {".pdf", ".md", ".txt"}
    skipped_count = 0
    
    # Walk through folder structure
    for root, dirs, files in os.walk(folder_path):
        root_path = Path(root)
        relative_path = root_path.relative_to(folder_path)
        
        # Determine doctype from folder name
        folder_name = relative_path.parts[0] if relative_path.parts else "documents"
        config = DOCTYPE_CONFIG.get(folder_name, {"doctype": "document", "safety_tag": "standard"})
        
        for file in files:
            filepath = root_path / file
            ext = filepath.suffix.lower()
            
            if ext not in supported_extensions:
                if verbose:
                    print(f"⏭️  Skipping unsupported file: {filepath.name}")
                continue
            
            # Check if already ingested
            relative_file = str(filepath.relative_to(folder_path))
            file_mtime = filepath.stat().st_mtime
            
            if skip_existing and relative_file in ingested_files:
                if ingested_files[relative_file] >= file_mtime:
                    if verbose:
                        print(f"⏭️  Skipping already ingested: {relative_file}")
                    skipped_count += 1
                    continue
            
            # Parse metadata from filename
            filename_meta = parse_filename_metadata(filepath.stem)
            
            # Merge metadata
            meta = {
                **config,
                **filename_meta
            }
            
            try:
                if verbose:
                    print(f"📄 Ingesting: {filepath.relative_to(folder_path)}")
                    print(f"   Type: {meta['doctype']}, Metadata: {filename_meta}")
                
                result = ingest_document(filepath, **meta)
                results.append({
                    "file": str(filepath.relative_to(folder_path)),
                    "status": "success",
                    "result": result
                })
                
                # Track successful ingestion
                ingested_files[relative_file] = file_mtime
                
                if verbose:
                    print(f"   ✅ Success: {result['stats']['chunks']} chunks")
                
            except Exception as e:
                results.append({
                    "file": str(filepath.relative_to(folder_path)),
                    "status": "error",
                    "error": str(e)
                })
                if verbose:
                    print(f"   ❌ Error: {e}")
    
    # Save tracking file
    if skip_existing:
        with open(tracking_path, 'w') as f:
            json.dump(ingested_files, f, indent=2)
    
    if verbose and skipped_count > 0:
        print(f"\n⏭️  Skipped {skipped_count} already ingested files")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Bulk ingest documents for Shopfloor Copilot")
    parser.add_argument("--folder", required=True, help="Folder containing documents")
    parser.add_argument("--app", default=DEFAULT_APP, help="Application name")
    parser.add_argument("--lang", default=DEFAULT_LANG, help="Language code")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages")
    parser.add_argument("--force", action="store_true", help="Re-ingest all files (ignore tracking)")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting bulk ingestion from: {args.folder}")
    print(f"📡 API endpoint: {INGEST_ENDPOINT}")
    if not args.force:
        print(f"⏭️  Skipping already ingested files (use --force to re-ingest all)")
    print()
    
    results = bulk_ingest(args.folder, verbose=not args.quiet, skip_existing=not args.force)
    
    # Summary
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")
    total_chunks = sum(r.get("result", {}).get("stats", {}).get("chunks", 0) for r in results if r["status"] == "success")
    
    print()
    print("=" * 60)
    print(f"📊 Ingestion Summary:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {error_count}")
    print(f"   📦 Total chunks: {total_chunks}")
    print("=" * 60)
    
    if error_count > 0:
        print("\n❌ Errors:")
        for r in results:
            if r["status"] == "error":
                print(f"   {r['file']}: {r['error']}")

if __name__ == "__main__":
    main()
