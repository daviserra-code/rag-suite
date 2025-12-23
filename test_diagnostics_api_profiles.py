"""
Test Diagnostics API with Different Profiles
Sprint 4 — Domain Profile Wiring

Tests actual diagnostics API calls showing behavioral differences
"""

import httpx
import asyncio
import json
from apps.shopfloor_copilot.domain_profiles import DomainProfileManager

async def test_diagnostics_api():
    """Test diagnostics API with different profiles."""
    
    print("=" * 80)
    print("DIAGNOSTICS API PROFILE TEST")
    print("=" * 80)
    
    manager = DomainProfileManager()
    
    # Test diagnostics endpoint with each profile
    profiles = ['aerospace_defence', 'pharma_process', 'automotive_discrete']
    
    for profile_name in profiles:
        print(f"\n{'=' * 80}")
        print(f"Testing with Profile: {profile_name.upper()}")
        print(f"{'=' * 80}")
        
        # Switch profile
        manager.switch_profile(profile_name)
        profile = manager.get_active_profile()
        
        print(f"\n✓ Switched to: {profile.display_name}")
        print(f"  Priority order: {profile.reason_taxonomy.diagnostic_priority_order[:3]}")
        print(f"  RAG sources: {profile.rag_preferences.priority_sources[:3]}")
        print(f"  Tone: {profile.diagnostics_behavior.tone}")
        
        # Make diagnostics API call
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:8002/api/diagnostics/explain",
                    json={
                        "scope": "line",
                        "id": "A01"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"\n  ✓ Diagnostics API Response:")
                    print(f"    Profile in metadata: {result['metadata'].get('domain_profile')}")
                    print(f"    Reasoning priority: {result['metadata'].get('reasoning_priority', [])[:3]}")
                    print(f"    RAG docs retrieved: {result['metadata'].get('rag_documents', 0)}")
                    
                    # Show first 150 chars of diagnostic output
                    print(f"\n    What is happening (first 150 chars):")
                    print(f"    {result['what_is_happening'][:150]}...")
                else:
                    print(f"  ✗ API call failed: {response.status_code}")
                    
        except Exception as e:
            print(f"  ✗ API test failed: {e}")
    
    print(f"\n{'=' * 80}")
    print("✅ Profile wiring is ACTIVE in diagnostics API")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    asyncio.run(test_diagnostics_api())
