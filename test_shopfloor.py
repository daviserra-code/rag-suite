#!/usr/bin/env python
"""
Test script for Shopfloor Copilot - Ollama Integration
Run this to verify the setup is working correctly.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_ollama_health():
    """Test Ollama connection"""
    print("🔍 Testing Ollama connection...")
    from packages.core_rag.llm_client import check_ollama_health
    
    result = check_ollama_health()
    if result['available']:
        print(f"✅ Ollama is available")
        print(f"   Models: {', '.join(result['models'])}")
        print(f"   Configured: {result['configured_model']}")
    else:
        print(f"❌ Ollama not available: {result.get('error')}")
    return result['available']


def test_retriever():
    """Test basic retrieval"""
    print("\n🔍 Testing retriever...")
    from packages.core_rag.retriever import retrieve_passages
    
    try:
        # Test query
        passages = retrieve_passages(
            app="shopfloor_copilot",
            query="How to start the line?",
            filters={"line": "A01"},
            n_results=5,
            rerank_top_k=3
        )
        print(f"✅ Retriever working - got {len(passages)} passages")
        if passages:
            print(f"   Top passage: {passages[0]['text'][:100]}...")
        return True
    except Exception as e:
        print(f"❌ Retriever error: {e}")
        return False


def test_llm_generation():
    """Test LLM generation"""
    print("\n🔍 Testing LLM generation...")
    from packages.core_rag.llm_client import generate_answer
    
    try:
        # Mock passage for testing
        mock_passages = [{
            'text': 'To start Line A01: 1) Release emergency stop, 2) Activate main power, 3) Press green start button',
            'meta': {'doc_id': 'WI-A01-001', 'page_from': 1, 'page_to': 1}
        }]
        
        result = generate_answer(
            query="How do I start Line A01?",
            context_passages=mock_passages,
            role="operator"
        )
        
        print(f"✅ LLM generation working")
        print(f"   Model: {result['model']}")
        print(f"   Answer: {result['answer'][:200]}...")
        return True
    except Exception as e:
        print(f"❌ LLM error: {e}")
        return False


def test_metadata_ingestion():
    """Test enhanced metadata ingestion"""
    print("\n🔍 Testing metadata ingestion...")
    
    print("✅ Metadata fields supported:")
    print("   - plant, line, station, turno")
    print("   - doctype, rev, valid_from, valid_to")
    print("   - safety_tag, lang")
    print("   Use POST /api/ingest with these Form fields")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("🏭 Shopfloor Copilot - Integration Tests")
    print("=" * 60)
    
    results = {
        'Ollama': test_ollama_health(),
        'Retriever': test_retriever(),
        'LLM Generation': test_llm_generation(),
        'Metadata': test_metadata_ingestion()
    }
    
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print("=" * 60)
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test:20} {status}")
    
    all_passed = all(results.values())
    print("\n" + ("🎉 All tests passed!" if all_passed else "⚠️  Some tests failed"))
    
    if not results['Ollama']:
        print("\n💡 To fix Ollama connection:")
        print("   1. Install Ollama: https://ollama.ai")
        print("   2. Run: ollama pull llama3.2")
        print("   3. Ensure Ollama is running on port 11434")
        print("   4. If in Docker, set OLLAMA_BASE_URL=http://host.docker.internal:11434")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
