from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any
import re
import os
import httpx
from datetime import datetime, timedelta
from sqlalchemy import text
from packages.core_rag.retriever import retrieve_and_answer, retrieve_passages, build_mes_filters
from packages.core_rag.hybrid_retriever import hybrid_retrieve, hybrid_retrieve_and_answer
from packages.core_rag.llm_client import generate_answer, check_ollama_health
from packages.tools.oee_sql_tool import query_oee_trend
from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine

router = APIRouter(tags=["ask"])


# ==================== Phase A: SQL Tools for Runtime Context ====================

def get_runtime_kpi_trend(minutes: int = 15, line_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get KPI trend from OPC historian for the last N minutes.
    Falls back to simulation data if OPC data unavailable.
    """
    try:
        engine = get_db_engine()
        with engine.begin() as conn:
            # Try OPC data first
            params = {"minutes": minutes}
            line_filter = ""
            if line_id:
                line_filter = "AND line = :line_id"
                params["line_id"] = line_id
            
            result = conn.execute(text(f"""
                SELECT 
                    ts,
                    line,
                    oee,
                    availability,
                    performance,
                    quality,
                    status
                FROM opc_kpi_samples
                WHERE ts >= NOW() - INTERVAL '{minutes} minutes'
                {line_filter}
                ORDER BY ts DESC
                LIMIT 100
            """), params)
            
            samples = []
            for row in result:
                samples.append({
                    "timestamp": row.ts.isoformat() if row.ts else None,
                    "line": row.line,
                    "oee": float(row.oee or 0),
                    "availability": float(row.availability or 0),
                    "performance": float(row.performance or 0),
                    "quality": float(row.quality or 0),
                    "status": row.status
                })
            
            if samples:
                return {
                    "source": "opc-historian",
                    "period_minutes": minutes,
                    "sample_count": len(samples),
                    "samples": samples
                }
            
            # Fallback to simulation data
            sim_result = conn.execute(text(f"""
                SELECT 
                    date,
                    shift,
                    line_id,
                    line_name,
                    oee,
                    availability,
                    performance,
                    quality
                FROM oee_line_shift
                WHERE date >= CURRENT_DATE - INTERVAL '1 day'
                {f"AND line_id = :line_id" if line_id else ""}
                ORDER BY date DESC, shift DESC
                LIMIT 10
            """), params)
            
            sim_samples = []
            for row in sim_result:
                sim_samples.append({
                    "date": row.date.isoformat() if row.date else None,
                    "shift": row.shift,
                    "line": row.line_id,
                    "line_name": row.line_name,
                    "oee": float(row.oee or 0),
                    "availability": float(row.availability or 0),
                    "performance": float(row.performance or 0),
                    "quality": float(row.quality or 0)
                })
            
            return {
                "source": "simulation-db",
                "note": "OPC data unavailable, using simulation baseline",
                "sample_count": len(sim_samples),
                "samples": sim_samples
            }
            
    except Exception as e:
        return {"error": str(e), "source": "error"}


def get_runtime_events(minutes: int = 60, line_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get events from OPC historian for the last N minutes.
    Falls back to simulation downtime events if OPC unavailable.
    """
    try:
        engine = get_db_engine()
        with engine.begin() as conn:
            # Try OPC events first
            params = {"minutes": minutes}
            line_filter = ""
            if line_id:
                line_filter = "AND line = :line_id"
                params["line_id"] = line_id
            
            result = conn.execute(text(f"""
                SELECT 
                    ts,
                    plant,
                    line,
                    station,
                    event_type,
                    payload
                FROM opc_events
                WHERE ts >= NOW() - INTERVAL '{minutes} minutes'
                {line_filter}
                ORDER BY ts DESC
                LIMIT 50
            """), params)
            
            events = []
            for row in result:
                events.append({
                    "timestamp": row.ts.isoformat() if row.ts else None,
                    "plant": row.plant,
                    "line": row.line,
                    "station": row.station,
                    "event_type": row.event_type,
                    "payload": row.payload
                })
            
            if events:
                return {
                    "source": "opc-events",
                    "period_minutes": minutes,
                    "event_count": len(events),
                    "events": events
                }
            
            # Fallback to simulation downtime events
            sim_result = conn.execute(text(f"""
                SELECT 
                    start_timestamp,
                    line_id,
                    loss_category,
                    duration_minutes,
                    units_lost
                FROM oee_downtime_events
                WHERE start_timestamp >= NOW() - INTERVAL '{minutes * 2} minutes'
                {f"AND line_id = :line_id" if line_id else ""}
                ORDER BY start_timestamp DESC
                LIMIT 20
            """), params)
            
            sim_events = []
            for row in sim_result:
                sim_events.append({
                    "timestamp": row.start_timestamp.isoformat() if row.start_timestamp else None,
                    "line": row.line_id,
                    "event_type": row.loss_category,
                    "duration_minutes": float(row.duration_minutes or 0),
                    "units_lost": int(row.units_lost or 0)
                })
            
            return {
                "source": "simulation-downtime",
                "note": "OPC events unavailable, using simulation downtime",
                "event_count": len(sim_events),
                "events": sim_events
            }
            
    except Exception as e:
        return {"error": str(e), "source": "error"}


async def get_runtime_context_async() -> Dict[str, Any]:
    """
    Fetch runtime context from OPC Studio snapshot endpoint.
    This provides the most recent plant state.
    """
    opc_url = os.getenv("OPC_STUDIO_URL", "http://opc-studio:8040")
    
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{opc_url}/snapshot")
            if response.status_code == 200:
                snapshot = response.json()
                if snapshot.get("ok"):
                    return {
                        "available": True,
                        "source": "opc-studio",
                        "data": snapshot.get("data", {})
                    }
    except Exception as e:
        pass
    
    return {"available": False, "source": "unavailable"}


def build_runtime_context_string(snapshot: Dict[str, Any], kpi_trend: Dict[str, Any], events: Dict[str, Any]) -> str:
    """
    Build a formatted string of runtime context for LLM injection.
    """
    context_parts = []
    
    # Current snapshot
    if snapshot.get("available"):
        data = snapshot.get("data", {})
        plant = data.get("plant", "Unknown")
        lines = data.get("lines", {})
        
        context_parts.append(f"=== LIVE PLANT STATE ({plant}) ===")
        for line_id, line_data in lines.items():
            oee = line_data.get("oee", 0)
            avail = line_data.get("availability", 0)
            perf = line_data.get("performance", 0)
            qual = line_data.get("quality", 0)
            status = line_data.get("status", "UNKNOWN")
            
            context_parts.append(f"Line {line_id}: OEE={oee:.1%} (A={avail:.1%}, P={perf:.1%}, Q={qual:.1%}) Status={status}")
            
            stations = line_data.get("stations", {})
            for st_id, st_data in stations.items():
                state = st_data.get("state", "UNKNOWN")
                alarms = st_data.get("alarms", [])
                if alarms:
                    context_parts.append(f"  Station {st_id}: {state} - Alarms: {alarms}")
                elif state != "RUNNING":
                    context_parts.append(f"  Station {st_id}: {state}")
    
    # Recent KPI trend
    if kpi_trend.get("sample_count", 0) > 0:
        context_parts.append(f"\n=== RECENT KPI TREND ({kpi_trend['period_minutes']}min) ===")
        samples = kpi_trend.get("samples", [])[:5]  # Last 5 samples
        for sample in samples:
            line = sample.get("line", "?")
            oee = sample.get("oee", 0)
            context_parts.append(f"{sample.get('timestamp', '?')[:16]} Line {line}: OEE={oee:.1%}")
    
    # Recent events
    if events.get("event_count", 0) > 0:
        context_parts.append(f"\n=== RECENT EVENTS ({events['period_minutes']}min) ===")
        event_list = events.get("events", [])[:10]  # Last 10 events
        for event in event_list:
            line = event.get("line", "?")
            station = event.get("station", "?")
            etype = event.get("event_type", "?")
            context_parts.append(f"{event.get('timestamp', '?')[:16]} {line}/{station}: {etype}")
    
    return "\n".join(context_parts) if context_parts else ""

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
async def ask_with_llm(req: AskWithLLMReq):
    """Enhanced endpoint - hybrid retrieval + Ollama LLM generation with runtime context injection"""
    
    # Valid lines in the database
    VALID_LINES = ['M10', 'B02', 'C03', 'D01', 'SMT1', 'WC01']
    
    # ========== Phase A: Inject Runtime Context ==========
    # Fetch runtime snapshot, KPI trends, and events
    runtime_enabled = os.getenv("RUNTIME_CONTEXT_ENABLED", "true").lower() in ("true", "1", "yes")
    runtime_context_text = ""
    runtime_metadata = {}
    
    if runtime_enabled:
        try:
            # Get runtime snapshot
            snapshot = await get_runtime_context_async()
            
            # Get KPI trend (last 15 minutes)
            kpi_trend = get_runtime_kpi_trend(minutes=15)
            
            # Get recent events (last 60 minutes)
            events = get_runtime_events(minutes=60)
            
            # Build context string for LLM
            runtime_context_text = build_runtime_context_string(snapshot, kpi_trend, events)
            
            runtime_metadata = {
                "runtime_context_available": snapshot.get("available", False),
                "kpi_samples": kpi_trend.get("sample_count", 0),
                "event_count": events.get("event_count", 0)
            }
            
        except Exception as e:
            runtime_metadata = {"runtime_context_error": str(e)}
    
    # ========== End Runtime Context Injection ==========
    
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
        result = retrieve_and_answer(req.app, req.query, req.filters or {})
        # Phase A: Inject runtime context metadata even in fallback path
        if runtime_metadata:
            result["runtime_context"] = runtime_metadata
        return result
    
    # Inject runtime context as a synthetic passage (if available)
    if runtime_context_text:
        passages.insert(0, {
            "text": runtime_context_text,
            "metadata": {
                "doc_id": "RUNTIME_CONTEXT",
                "source": "OPC Studio Live Data",
                "type": "runtime"
            },
            "score": 1.0,
            "rerank_score": 1.0
        })
    
    # Generate answer with Ollama (now includes runtime context)
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
        "retrieval_method": "hybrid_bm25_vector_rrf",
        "runtime_context": runtime_metadata  # Phase A: Include runtime context metadata
    }

@router.get("/health/ollama")
def ollama_health():
    """Check Ollama availability"""
    return check_ollama_health()
