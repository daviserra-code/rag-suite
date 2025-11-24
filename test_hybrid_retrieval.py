"""
Test script for Hybrid Retrieval System
Tests both keyword-based queries (BM25) and semantic queries (embeddings)
"""
import requests
import json

BASE_URL = "http://localhost:8010/api"

# Test queries
test_queries = [
    {
        "name": "Keyword Query - OEE",
        "query": "What is OEE?",
        "description": "Should match exact keyword 'OEE' with BM25"
    },
    {
        "name": "Keyword Query - FPY",
        "query": "FPY calculation",
        "description": "Should match exact acronym 'FPY'"
    },
    {
        "name": "Keyword Query - Station S10",
        "query": "S10 procedures",
        "description": "Should match exact station code 'S10'"
    },
    {
        "name": "Semantic Query - Equipment Efficiency",
        "query": "How to improve equipment efficiency?",
        "description": "Should match semantic concepts related to OEE/efficiency"
    },
    {
        "name": "Semantic Query - Quality",
        "query": "Reducing defect rates",
        "description": "Should match quality-related content semantically"
    },
    {
        "name": "Hybrid Query - Safety Emergency",
        "query": "emergency stop procedure S10",
        "description": "Combines exact keyword (S10) with semantic (emergency)"
    }
]

def test_hybrid_retrieval():
    print("=" * 80)
    print("HYBRID RETRIEVAL SYSTEM TEST")
    print("=" * 80)
    print()
    
    for test in test_queries:
        print(f"Test: {test['name']}")
        print(f"Query: '{test['query']}'")
        print(f"Description: {test['description']}")
        print("-" * 80)
        
        try:
            response = requests.post(
                f"{BASE_URL}/ask/llm",
                json={
                    "app": "rag_documents",
                    "query": test['query'],
                    "role": "operator",
                    "use_llm": True
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Status: {response.status_code}")
                print(f"✓ Retrieval Method: {result.get('retrieval_method', 'N/A')}")
                print(f"✓ Hits: {result.get('hits', 0)}")
                print(f"✓ Model: {result.get('model', 'N/A')}")
                
                # Show top 3 citations with scores
                citations = result.get('citations', [])[:3]
                if citations:
                    print(f"✓ Top 3 Citations:")
                    for i, cite in enumerate(citations, 1):
                        score = cite.get('score', 0)
                        doc_id = cite.get('doc_id', 'N/A')
                        print(f"  {i}. {doc_id} | Score: {score}")
                
                # Show answer preview
                answer = result.get('answer', '')
                answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"✓ Answer Preview: {answer_preview}")
                
            else:
                print(f"✗ Error: Status {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"✗ Exception: {str(e)}")
        
        print()
        print()

if __name__ == "__main__":
    test_hybrid_retrieval()
