import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment for testing
os.environ['CHROMA_HOST'] = 'localhost'
os.environ['CHROMA_PORT'] = '8001'

print("Environment:")
print(f"  CHROMA_HOST={os.getenv('CHROMA_HOST')}")
print(f"  CHROMA_PORT={os.getenv('CHROMA_PORT')}")

try:
    from packages.core_rag.chroma_client import get_chroma_client
    
    print("\nConnecting to Chroma...")
    client = get_chroma_client()
    
    print(f"  Client: {client}")
    
    collections = client.list_collections()
    print(f"\nCollections found: {len(collections)}")
    for coll in collections:
        print(f"  - {coll.name} ({coll.count()} documents)")
    
    # Try to get shopfloor_docs
    print("\nTrying to get 'shopfloor_docs' collection...")
    coll = client.get_collection('shopfloor_docs')
    count = coll.count()
    print(f"  ✅ Success! Collection has {count} documents")
    
    # Test query
    if count > 0:
        print("\nTesting query...")
        results = coll.query(query_texts=["work instruction"], n_results=3)
        print(f"  Query returned {len(results['ids'][0])} results")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
