from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any
import re
from packages.core_rag.retriever import retrieve_and_answer, retrieve_passages, build_mes_filters
from packages.core_rag.hybrid_retriever import hybrid_retrieve, hybrid_retrieve_and_answer
from packages.core_rag.llm_client import generate_answer, check_ollama_health
from packages.tools.oee_sql_tool import query_oee_trend

router = APIRouter(tags=["ask"])

def normalize_filters(filters: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Convert simple dict filters to ChromaDB $and format if needed.
    
    ChromaDB requires: {"$and": [{"field1": "value1"}, {"field2": "value2"}]}
    Instead of: {"field1": "value1", "field2": "value2"}
    """
    if not filters or len(filters) <= 1:
        return filters
    
    # Convert to $and format
    return {
        "$and": [{k: v} for k, v in filters.items()]
    }

UserRole = Literal["operator", "line_manager", "quality_manager", "plant_manager"]

class AskReq(BaseModel):
    app: str
    query: str
    filters: dict | None = None

class AskWithLLMReq(BaseModel):
    app: str
    query: str
    filters: dict | None = None
    role: UserRole = "operator"
    use_llm: bool = True

@router.post("/ask")
def ask(req: AskReq):
    """Legacy endpoint - simple retrieval with extractive answer"""
    # retrieve_and_answer will call build_mes_filters internally
    return retrieve_and_answer(req.app, req.query, req.filters or {})

@router.post("/ask/llm")
def ask_with_llm(req: AskWithLLMReq):
    """Enhanced endpoint - hybrid retrieval + Ollama LLM generation"""
    
    # Valid lines in the database
    VALID_LINES = ['M10', 'B02', 'C03', 'D01', 'SMT1', 'WC01']
    
    # Check if query is about OEE trends - extract line ID
    oee_pattern = r'(oee|overall equipment effectiveness).*(line|' + '|'.join(VALID_LINES) + r')'
    match = re.search(oee_pattern, req.query.lower())
    
    if match:
        # Extract line ID from query
        line_pattern = r'\b(' + '|'.join(VALID_LINES) + r')\b'
        line_match = re.search(line_pattern, req.query, re.IGNORECASE)
        
        if line_match:
            line_id = line_match.group(1).upper()
            print(f"[OEE Query Detected] Line: {line_id}")
            
            try:
                # Query OEE data from database
                oee_data = query_oee_trend(line_id=line_id, days=7)
                
                if "error" not in oee_data:
                    # Create a summarized context for the LLM
                    summary_context = f"""
OEE Analysis for {oee_data['line_name']} ({oee_data['period']}):

Average Metrics:
- OEE: {oee_data['averages']['oee']:.1%}
- Availability: {oee_data['averages']['availability']:.1%}
- Performance: {oee_data['averages']['performance']:.1%}
- Quality: {oee_data['averages']['quality']:.1%}
- Total Downtime: {oee_data['averages']['total_downtime_min']:.0f} minutes

Top Loss Categories:
"""
                    for loss in oee_data['top_losses']:
                        summary_context += f"- {loss['category']}: {loss['downtime_min']:.0f} min ({loss['occurrences']} occurrences)\n"
                    
                    summary_context += "\nRecent Trend (last 5 shifts):\n"
                    for record in oee_data['recent_data'][:5]:
                        summary_context += f"- {record['date']} {record['shift']}: OEE {record['oee']:.1%}, Main Loss: {record['main_loss']}\n"
                    
                    # Generate answer with summarized OEE data
                    llm_result = generate_answer(
                        query=req.query,
                        context_passages=[{"text": summary_context, "metadata": {"doc_id": "OEE Database"}}],
                        role=req.role
                    )
                    
                    return {
                        "answer": llm_result.get("answer", ""),
                        "citations": [{"doc_id": "OEE Database", "source": "PostgreSQL", "type": "live_data"}],
                        "model": llm_result.get("model", ""),
                        "filters_applied": req.filters or {},
                        "hits": 1,
                        "role": req.role,
                        "retrieval_method": "oee_sql_query",
                        "oee_data": oee_data  # Include full data for potential visualization
                    }
                else:
                    # OEE query failed - provide helpful error with available lines
                    available_lines = ", ".join(VALID_LINES)
                    error_msg = f"❌ Line '{line_id}' not found in OEE database.\n\n✅ Available lines: {available_lines}\n\nPlease try one of these lines."
                    return {
                        "answer": error_msg,
                        "citations": [{"doc_id": "System", "type": "error"}],
                        "model": "",
                        "filters_applied": req.filters or {},
                        "hits": 0,
                        "role": req.role,
                        "retrieval_method": "error"
                    }
            except Exception as e:
                print(f"[OEE Query Error] {str(e)}")
                # Fall through to regular retrieval
    
    # Regular document retrieval flow
    # Build MES filters (adds app field)
    mes_filters = build_mes_filters(req.app, req.filters or {})
    
    # Normalize filters for ChromaDB (convert to $and if multiple fields)
    normalized_filters = normalize_filters(mes_filters)
    
    # Use hybrid retrieval (BM25 + Dense Embeddings with RRF)
    passages = hybrid_retrieve(
        query=req.query,
        collection_name="rag_core",  # Default collection name
        top_k=10,
        rerank=True,
        filters=normalized_filters
    )
    
    if not req.use_llm or not passages:
        # Fallback to legacy behavior
        # NOTE: Don't rebuild filters - retrieve_and_answer will call build_mes_filters itself
        return retrieve_and_answer(req.app, req.query, req.filters or {})
    
    # Generate answer with Ollama
    llm_result = generate_answer(
        query=req.query,
        context_passages=passages,
        role=req.role
    )
    
    # Build citations
    citations = []
    for p in passages[:3]:
        m = p.get("metadata", {})
        citations.append({
            "doc_id": m.get("doc_id", "?"),
            "pages": f"{m.get('page_from','?')}-{m.get('page_to','?')}",
            "url": m.get("source_url", ""),
            "score": round(p.get("rerank_score", p.get("rrf_score", 0.0)), 3),
            "plant": m.get("plant", ""),
            "line": m.get("line", ""),
            "station": m.get("station", "")
        })
    
    return {
        "answer": llm_result.get("answer", ""),
        "citations": citations,
        "model": llm_result.get("model", ""),
        "filters_applied": req.filters or {},
        "hits": len(passages),
        "role": req.role,
        "retrieval_method": "hybrid_bm25_vector_rrf"
    }

@router.get("/health/ollama")
def ollama_health():
    """Check Ollama availability"""
    return check_ollama_health()
