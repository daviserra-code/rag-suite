import httpx
import time

# Test Ollama response time
start = time.time()
client = httpx.Client(base_url='http://host.docker.internal:11434', timeout=120.0)
resp = client.post('/api/generate', json={
    'model': 'llama3.2:latest',
    'prompt': 'What is OEE? Explain the calculation formula in detail.',
    'stream': False
})
elapsed = time.time() - start

data = resp.json()
response_text = data.get('response', '')

print(f"Time taken: {elapsed:.1f}s")
print(f"Response length: {len(response_text)} chars")
print(f"Tokens generated: {data.get('eval_count', 0)}")
print(f"Tokens per second: {data.get('eval_count', 0) / (data.get('eval_duration', 1) / 1e9):.1f}")
print(f"\nResponse preview:\n{response_text[:200]}...")
