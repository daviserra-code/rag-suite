import requests

print("=" * 70)
print("Testing Newly Ingested Documents")
print("=" * 70)

# Test 1: Query the S10 document
print("\n📋 Test 1: S10 Assembly Line Operating Procedure")
print("-" * 70)
r = requests.post('http://localhost:8010/api/ask/llm', json={
    'app': 'shopfloor',
    'query': 'What are the operating procedures for S10 Assembly Line?'
})
result = r.json()
print(f"✅ Status: {r.status_code}")
print(f"📊 Hits: {result['hits']}")
print(f"📄 Top source: {result['citations'][0]['url']}")
print(f"\n💬 Answer preview:\n{result['answer'][:300]}...\n")

# Test 2: Count total documents
print("\n📚 Test 2: Total Document Count")
print("-" * 70)
r = requests.post('http://localhost:8010/api/ask/llm', json={
    'app': 'shopfloor',
    'query': 'assembly'
})
result = r.json()
print(f"📊 Total hits for 'assembly': {result['hits']}")
print(f"📄 Unique sources:")
sources = set(c['url'] for c in result['citations'])
for i, src in enumerate(sources, 1):
    print(f"  {i}. {src}")

# Test 3: Test with filters
print("\n🔍 Test 3: Filter by Station S110")
print("-" * 70)
r = requests.post('http://localhost:8010/api/ask/llm', json={
    'app': 'shopfloor',
    'query': 'assembly steps',
    'filters': {'station': 'S110'}
})
result = r.json()
print(f"✅ Status: {r.status_code}")
print(f"📊 Filtered hits: {result['hits']}")
print(f"🏷️  Filters applied: {result.get('filters_applied', {})}")
if result.get('citations'):
    print(f"📄 Sources (S110 only):")
    for i, c in enumerate(result['citations'][:3], 1):
        print(f"  {i}. {c['url']} (station: {c.get('station', 'N/A')})")

# Test 4: Safety documents
print("\n⚠️  Test 4: Safety Documents (Critical)")
print("-" * 70)
r = requests.post('http://localhost:8010/api/ask/llm', json={
    'app': 'shopfloor',
    'query': 'lockout tagout',
    'filters': {'safety_tag': 'critical'}
})
result = r.json()
print(f"✅ Status: {r.status_code}")
print(f"📊 Safety docs found: {result['hits']}")
if result.get('citations'):
    print(f"📄 Top safety document: {result['citations'][0]['url']}")
    print(f"💬 Answer preview:\n{result['answer'][:250]}...\n")

print("\n" + "=" * 70)
print("✅ All Tests Complete!")
print("=" * 70)
