"""
Diagnostics Router
Sprint 3 — AI-Grounded Diagnostics & Explainability

API endpoints for explainable diagnostics based on semantic runtime data.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
import logging

from packages.diagnostics import DiagnosticsExplainer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])

# Initialize diagnostics explainer
explainer = DiagnosticsExplainer()


class ExplainRequest(BaseModel):
    """Request model for diagnostic explanation."""
    scope: Literal["line", "station"]
    id: str  # Line ID (e.g., "A01") or Station ID (e.g., "ST18")


class ExplainResponse(BaseModel):
    """Response model for diagnostic explanation."""
    ok: bool
    scope: str
    equipment_id: str
    what_is_happening: str
    why_this_is_happening: str
    what_to_do_now: str
    what_to_check_next: str
    metadata: dict


@router.post("/explain", response_model=ExplainResponse)
async def explain_situation(request: ExplainRequest):
    """
    Generate AI-grounded, explainable diagnostic for a line or station.
    
    Mandatory Flow:
    1. Fetch semantic snapshot (authoritative truth)
    2. Extract relevant subset based on scope
    3. Identify active loss_category
    4. Query Chroma for procedures (RAG)
    5. Build structured prompt
    6. Call LLM
    7. Return structured explanation
    
    Args:
        request: ExplainRequest with scope and equipment ID
    
    Returns:
        Structured diagnostic with 4 sections:
        - what_is_happening: Runtime evidence (facts only)
        - why_this_is_happening: Reasoned explanation
        - what_to_do_now: Procedures from RAG
        - what_to_check_next: Actionable checklist
    
    Guardrails:
    - Uses ONLY data from semantic snapshot
    - Never invents values or causes
    - Clearly separates facts from recommendations
    - States "insufficient data" when evidence is lacking
    """
    try:
        logger.info(f"Diagnostic request: {request.scope} {request.id}")
        
        # Validate scope
        if request.scope not in ["line", "station"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scope: {request.scope}. Must be 'line' or 'station'."
            )
        
        # Sprint 4: Load active profile and pass explicitly
        try:
            from apps.shopfloor_copilot.domain_profiles import get_active_profile
            profile = get_active_profile()
            logger.info(f"Using domain profile: {profile.display_name}")
        except Exception as e:
            logger.warning(f"Could not load profile: {e}")
            profile = None
        
        # Generate diagnostic explanation with explicit profile context
        result = await explainer.explain_situation(
            scope=request.scope,
            equipment_id=request.id,
            profile=profile
        )
        
        # Check for errors
        if result.get('metadata', {}).get('error'):
            raise HTTPException(
                status_code=503,
                detail=result['what_is_happening']
            )
        
        return ExplainResponse(
            ok=True,
            scope=request.scope,
            equipment_id=request.id,
            what_is_happening=result['what_is_happening'],
            why_this_is_happening=result['why_this_is_happening'],
            what_to_do_now=result['what_to_do_now'],
            what_to_check_next=result['what_to_check_next'],
            metadata=result['metadata']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Diagnostic generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Diagnostic generation failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for diagnostics service."""
    return {
        "ok": True,
        "service": "diagnostics",
        "sprint": "Sprint 3 — AI-Grounded Diagnostics",
        "capabilities": [
            "explain_situation",
            "loss_category_analysis",
            "rag_retrieval",
            "structured_output"
        ]
    }
