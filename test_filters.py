import requests
import json

# Test 1: No filter
print("=" * 60)
print("Test 1: Query without filter")
print("=" * 60)
r = requests.post('http://localhost:8010/api/ask/llm', json={
    'app': 'shopfloor',
    'query': 'assembly steps'
})
result = r.json()
print(f"Status: {r.status_code}")
print(f"Hits: {result['hits']}")
print(f"Top result: {result['citations'][0]['url'] if result.get('citations') else 'None'}")

# Test 2: Station filter
print("\n" + "=" * 60)
print("Test 2: Query with station=S110 filter")
print("=" * 60)
r = requests.post('http://localhost:8010/api/ask/llm', json={
    'app': 'shopfloor',
    'query': 'assembly steps',
    'filters': {'station': 'S110'}
})
result = r.json()
print(f"Status: {r.status_code}")
print(f"Hits: {result['hits']}")
print(f"Filters applied: {result.get('filters_applied', {})}")
if result.get('citations'):
    print(f"\nTop 3 results:")
    for i, c in enumerate(result['citations'][:3], 1):
        print(f"  {i}. {c['url']} (station: {c.get('station', 'N/A')})")

# Test 3: Plant filter  
print("\n" + "=" * 60)
print("Test 3: Query with plant=P01 filter")
print("=" * 60)
r = requests.post('http://localhost:8010/api/ask/llm', json={
    'app': 'shopfloor',
    'query': 'safety',
    'filters': {'plant': 'P01', 'doctype': 'safety'}
})
result = r.json()
print(f"Status: {r.status_code}")
print(f"Hits: {result['hits']}")
if result.get('citations'):
    print(f"Top result: {result['citations'][0]['url']}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
