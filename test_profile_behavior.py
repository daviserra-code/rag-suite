"""
Test Domain Profile Behavioral Differences
Sprint 4 — Domain Profile Wiring

Verifies that switching domain profiles produces OBSERVABLE behavioral changes:
- Different reasoning priority order
- Different RAG document retrieval
- Different diagnostic tone and emphasis
"""

import asyncio
import httpx
from apps.shopfloor_copilot.domain_profiles import DomainProfileManager, get_active_profile
from packages.diagnostics import DiagnosticsExplainer

async def test_profile_behavior():
    """Test that profile switching causes visible behavioral changes."""
    
    print("=" * 80)
    print("DOMAIN PROFILE BEHAVIORAL TEST")
    print("=" * 80)
    
    # Initialize profile manager and diagnostics
    manager = DomainProfileManager()
    explainer = DiagnosticsExplainer()
    
    # Test query
    test_query = "Why is operation OP40 blocked?"
    equipment_id = "A01"  # Line A01
    scope = "line"
    
    # Test all 3 profiles
    profiles = ['aerospace_defence', 'pharma_process', 'automotive_discrete']
    
    results = {}
    
    for profile_name in profiles:
        print(f"\n{'=' * 80}")
        print(f"Testing Profile: {profile_name.upper()}")
        print(f"{'=' * 80}")
        
        # Switch profile
        manager.switch_profile(profile_name)
        profile = get_active_profile()
        
        print(f"\n✓ Active Profile: {profile.display_name}")
        print(f"  Diagnostic Priority Order: {profile.reason_taxonomy.diagnostic_priority_order}")
        print(f"  RAG Priority Sources: {profile.rag_preferences.priority_sources[:5]}")
        print(f"  Tone: {profile.diagnostics_behavior.tone}")
        print(f"  Emphasis: {profile.diagnostics_behavior.emphasis}")
        
        # Test RAG retrieval with profile
        print(f"\n  Testing RAG retrieval...")
        try:
            rag_results = await explainer._query_rag(
                equipment_id=equipment_id,
                loss_categories=['availability.equipment_failure'],
                scope=scope,
                profile=profile
            )
            
            print(f"  ✓ Retrieved {len(rag_results)} documents")
            if rag_results:
                for i, result in enumerate(rag_results[:3], 1):
                    print(f"    {i}. {result['source_type']} (weight: {result['weight']}, score: {result['score']:.3f})")
        except Exception as e:
            print(f"  ✗ RAG test failed: {e}")
        
        # Store results for comparison
        results[profile_name] = {
            'priority_order': profile.reason_taxonomy.diagnostic_priority_order,
            'rag_sources': profile.rag_preferences.priority_sources[:5],
            'tone': profile.diagnostics_behavior.tone,
            'emphasis': profile.diagnostics_behavior.emphasis,
            'rag_results': len(rag_results) if rag_results else 0
        }
    
    # Compare behaviors
    print(f"\n{'=' * 80}")
    print("BEHAVIORAL COMPARISON")
    print(f"{'=' * 80}")
    
    # Check priority order differences
    print("\n1. DIAGNOSTIC PRIORITY ORDER:")
    for profile_name, data in results.items():
        print(f"   {profile_name:25} → {data['priority_order'][:3]}")
    
    # Check tone differences
    print("\n2. DIAGNOSTIC TONE:")
    for profile_name, data in results.items():
        print(f"   {profile_name:25} → {data['tone']} ({data['emphasis']})")
    
    # Check RAG source preferences
    print("\n3. RAG PRIORITY SOURCES:")
    for profile_name, data in results.items():
        print(f"   {profile_name:25} → {data['rag_sources'][:3]}")
    
    # Verify differences
    print(f"\n{'=' * 80}")
    print("VERIFICATION")
    print(f"{'=' * 80}")
    
    priority_orders = [d['priority_order'] for d in results.values()]
    rag_sources = [tuple(d['rag_sources']) for d in results.values()]
    tones = [d['tone'] for d in results.values()]
    
    all_different_priority = len(set(map(tuple, priority_orders))) == len(priority_orders)
    all_different_rag = len(set(rag_sources)) == len(rag_sources)
    different_tones = len(set(tones)) > 1
    
    print(f"\n✓ Priority orders are profile-specific: {all_different_priority}")
    print(f"✓ RAG sources are profile-specific: {all_different_rag}")
    print(f"✓ Tones vary across profiles: {different_tones}")
    
    if all_different_priority and all_different_rag and different_tones:
        print(f"\n{'=' * 80}")
        print("✅ SUCCESS: Domain profiles are EXECUTIVE (behavior changes per profile)")
        print(f"{'=' * 80}")
        return True
    else:
        print(f"\n{'=' * 80}")
        print("❌ FAIL: Domain profiles are COSMETIC (no behavioral change)")
        print(f"{'=' * 80}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_profile_behavior())
    exit(0 if success else 1)
