import os
import httpx
from typing import Dict, List, Any, Literal

# Role-specific system prompts
ROLE_PROMPTS = {
    "operator": """You are a helpful shopfloor assistant for manufacturing operators.
Provide clear, step-by-step instructions based on work instructions and SOPs.
Focus on safety, quality, and operational procedures.
Always cite your sources using [doc_id] notation.""",
    
    "line_manager": """You are an AI assistant for manufacturing line managers.
Provide insights on line performance, bottlenecks, and optimization opportunities.
Focus on OEE, throughput, downtime analysis, and resource allocation.
Always cite your sources using [doc_id] notation.""",
    
    "quality_manager": """You are an AI assistant for quality managers.
Provide analysis on quality issues, defect patterns, and root causes.
Focus on FPY, defect trends, corrective actions, and quality procedures.
Always cite your sources using [doc_id] notation.""",
    
    "plant_manager": """You are an AI assistant for plant managers.
Provide strategic insights on overall plant performance and optimization.
Focus on KPIs, trends, strategic recommendations, and cross-functional issues.
Always cite your sources using [doc_id] notation."""
}

UserRole = Literal["operator", "line_manager", "quality_manager", "plant_manager"]


def get_ollama_client() -> httpx.Client:
    """Get configured Ollama HTTP client"""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    return httpx.Client(base_url=base_url, timeout=60.0)


def generate_answer(
    query: str,
    context_passages: List[Dict[str, Any]],
    role: UserRole = "operator",
    temperature: float = 0.3
) -> Dict[str, Any]:
    """
    Generate an answer using Ollama based on retrieved context.
    
    Args:
        query: User's question
        context_passages: List of retrieved passages with metadata
        role: User role for context-aware prompting
        temperature: LLM temperature (0.0-1.0)
        
    Returns:
        Dict with 'answer' and 'model' keys
    """
    model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    system_prompt = ROLE_PROMPTS.get(role, ROLE_PROMPTS["operator"])
    
    # Build context from passages
    context_blocks = []
    for idx, passage in enumerate(context_passages[:5], 1):
        # Handle both old format (meta) and new format (metadata)
        meta = passage.get("metadata") or passage.get("meta", {})
        doc_id = meta.get("doc_id", "unknown")
        text = passage.get("text", "")
        context_blocks.append(f"[{doc_id}] {text}")
    
    context_text = "\n\n".join(context_blocks) if context_blocks else "No relevant context found."
    
    # Check if first passage is RUNTIME_CONTEXT (Phase A runtime injection)
    has_runtime = (len(context_passages) > 0 and 
                   context_passages[0].get("metadata", {}).get("doc_id") == "RUNTIME_CONTEXT")
    
    # Build prompt with guardrails
    if has_runtime:
        runtime_text = context_passages[0].get("text", "")
        kb_context = "\n\n".join(context_blocks[1:]) if len(context_blocks) > 1 else "No additional documentation found."
        user_prompt = f"""RUNTIME CONTEXT (Live Plant Data):

{runtime_text}

Knowledge Base Context:

{kb_context}

Question: {query}

IMPORTANT GUARDRAILS:
- Only reference line/station IDs explicitly listed in the RUNTIME CONTEXT above
- If runtime data is unavailable, state this clearly and use knowledge base only
- Prioritize runtime data for current status questions
- Reference sources using [doc_id] or [RUNTIME_CONTEXT] notation

Answer based on both runtime data and knowledge base:"""
    else:
        user_prompt = f"""Context from knowledge base:

{context_text}

Question: {query}

Answer the question based on the context above. If the context doesn't contain enough information, say so clearly. Always reference the source documents using [doc_id] notation."""
    
    print(f"[LLM] Prompt size: {len(user_prompt)} chars, {len(context_passages)} passages, Model: {model}")
    print(f"[LLM] Sending request to Ollama...")
    
    try:
        import time
        start_time = time.time()
        
        client = get_ollama_client()
        response = client.post(
            "/api/generate",
            json={
                "model": model,
                "prompt": user_prompt,
                "system": system_prompt,
                "temperature": temperature,
                "stream": False
            }
        )
        response.raise_for_status()
        data = response.json()
        
        elapsed = time.time() - start_time
        tokens = data.get("eval_count", 0)
        print(f"[LLM] Response received in {elapsed:.1f}s ({tokens} tokens, {tokens/elapsed:.1f} tok/s)")
        
        return {
            "answer": data.get("response", "").strip(),
            "model": model,
            "done": data.get("done", False)
        }
        
    except httpx.HTTPError as e:
        # Fallback if Ollama is not available
        if os.getenv("ENABLE_CLOUD_FALLBACK", "false").lower() == "true":
            return {
                "answer": "Cloud fallback not yet implemented. Please ensure Ollama is running.",
                "model": "fallback",
                "error": str(e)
            }
        else:
            return {
                "answer": f"Error connecting to Ollama: {str(e)}. Please ensure Ollama is running at {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}",
                "model": "error",
                "error": str(e)
            }


def generate_answer_streaming(
    query: str,
    context_passages: List[Dict[str, Any]],
    role: UserRole = "operator",
    temperature: float = 0.3
):
    """
    Generate an answer using Ollama with streaming response.
    Yields chunks of text as they arrive.
    """
    model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    system_prompt = ROLE_PROMPTS.get(role, ROLE_PROMPTS["operator"])
    
    # Build context from passages
    context_blocks = []
    for idx, passage in enumerate(context_passages[:5], 1):
        # Handle both old format (meta) and new format (metadata)
        meta = passage.get("metadata") or passage.get("meta", {})
        doc_id = meta.get("doc_id", "unknown")
        text = passage.get("text", "")
        context_blocks.append(f"[{doc_id}] {text}")
    
    context_text = "\n\n".join(context_blocks) if context_blocks else "No relevant context found."
    
    # Build prompt
    user_prompt = f"""Context from knowledge base:

{context_text}

Question: {query}

Answer the question based on the context above. If the context doesn't contain enough information, say so clearly. Always reference the source documents using [doc_id] notation."""
    
    try:
        client = get_ollama_client()
        with client.stream(
            "POST",
            "/api/generate",
            json={
                "model": model,
                "prompt": user_prompt,
                "system": system_prompt,
                "temperature": temperature,
                "stream": True
            }
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                        
    except httpx.HTTPError as e:
        yield f"Error: {str(e)}"


def check_ollama_health() -> Dict[str, Any]:
    """Check if Ollama is available and responsive"""
    try:
        client = get_ollama_client()
        response = client.get("/api/tags")
        response.raise_for_status()
        models = response.json().get("models", [])
        
        return {
            "available": True,
            "models": [m.get("name") for m in models],
            "configured_model": os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "configured_model": os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        }
