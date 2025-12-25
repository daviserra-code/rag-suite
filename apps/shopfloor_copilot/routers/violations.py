"""
Violations Lifecycle Router
Sprint 4 Extension - STEP 3.1

API endpoints for violation lifecycle management:
- Acknowledge violations
- Justify violations with evidence
- Resolve violations
- Query violation timeline and history
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import uuid

from packages.violation_audit import get_violation_persistence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/violations", tags=["violations"])


class AcknowledgmentRequest(BaseModel):
    """Request model for acknowledging a violation."""
    ack_type: str  # 'acknowledged', 'justified', 'false_positive', 'resolved'
    comment: Optional[str] = None
    evidence_ref: Optional[str] = None
    ack_by: str = "demo_user"  # Default user


class ResolveRequest(BaseModel):
    """Request model for resolving a violation."""
    comment: Optional[str] = None
    ack_by: str = "demo_user"


@router.post("/{violation_id}/ack")
async def acknowledge_violation(violation_id: str, request: AcknowledgmentRequest):
    """
    Add acknowledgment to a violation.
    
    Acknowledgment types:
    - acknowledged: User has seen the violation
    - justified: Temporary acceptance with reason (requires comment)
    - false_positive: Not actually a violation
    - resolved: Issue fixed (closes violation)
    
    Args:
        violation_id: UUID of violation
        request: Acknowledgment details
    
    Returns:
        Acknowledgment confirmation with updated state
    """
    try:
        persistence = get_violation_persistence()
        
        # Validate violation exists
        violation = persistence.get_violation_by_id(uuid.UUID(violation_id))
        if not violation:
            raise HTTPException(status_code=404, detail=f"Violation {violation_id} not found")
        
        # Validate justification has comment
        if request.ack_type == 'justified' and not request.comment:
            raise HTTPException(
                status_code=400,
                detail="Justification requires a comment explaining the reason"
            )
        
        # Add acknowledgment
        ack_id = persistence.add_acknowledgment(
            violation_id=uuid.UUID(violation_id),
            ack_by=request.ack_by,
            ack_type=request.ack_type,
            comment=request.comment,
            evidence_ref=request.evidence_ref
        )
        
        if not ack_id:
            raise HTTPException(status_code=500, detail="Failed to add acknowledgment")
        
        # Get updated timeline
        timeline = persistence.get_violation_timeline(uuid.UUID(violation_id))
        
        return {
            "ok": True,
            "ack_id": ack_id,
            "violation_id": violation_id,
            "ack_type": request.ack_type,
            "state": timeline['state'] if timeline else 'UNKNOWN',
            "message": f"Violation {request.ack_type}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge violation {violation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{violation_id}/resolve")
async def resolve_violation(violation_id: str, request: ResolveRequest):
    """
    Resolve a violation (close it).
    
    Resolution should only occur when the underlying condition is fixed.
    This adds a 'resolved' acknowledgment and sets ts_end.
    
    Note: In production, this endpoint should verify that expectations
    no longer fail before allowing resolution. For now, it's manual.
    
    Args:
        violation_id: UUID of violation
        request: Resolution details
    
    Returns:
        Resolution confirmation
    """
    try:
        persistence = get_violation_persistence()
        
        # Validate violation exists
        violation = persistence.get_violation_by_id(uuid.UUID(violation_id))
        if not violation:
            raise HTTPException(status_code=404, detail=f"Violation {violation_id} not found")
        
        # Check if already resolved
        if violation.get('ts_end'):
            raise HTTPException(
                status_code=400,
                detail="Violation already resolved"
            )
        
        # Resolve violation
        success = persistence.resolve_violation(
            violation_id=uuid.UUID(violation_id),
            ack_by=request.ack_by,
            comment=request.comment
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to resolve violation")
        
        return {
            "ok": True,
            "violation_id": violation_id,
            "state": "RESOLVED",
            "message": "Violation resolved successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve violation {violation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{violation_id}/timeline")
async def get_violation_timeline(violation_id: str):
    """
    Get full timeline for a violation.
    
    Returns:
    - Violation data
    - All acknowledgments in chronological order
    - Current state (OPEN, ACKNOWLEDGED, JUSTIFIED, RESOLVED)
    
    Args:
        violation_id: UUID of violation
    
    Returns:
        Complete violation timeline with state
    """
    try:
        persistence = get_violation_persistence()
        
        timeline = persistence.get_violation_timeline(uuid.UUID(violation_id))
        
        if not timeline:
            raise HTTPException(status_code=404, detail=f"Violation {violation_id} not found")
        
        return {
            "ok": True,
            **timeline
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get timeline for {violation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_violations(
    station: Optional[str] = None,
    profile: Optional[str] = None,
    blocking_only: bool = False
):
    """
    Get all active violations.
    
    Args:
        station: Optional filter by station
        profile: Optional filter by profile
        blocking_only: If True, only return blocking violations
    
    Returns:
        List of active violations with states
    """
    try:
        persistence = get_violation_persistence()
        
        violations = persistence.get_active_violations(
            station=station,
            profile=profile,
            blocking_only=blocking_only
        )
        
        # Enrich with states
        enriched = []
        for violation in violations:
            timeline = persistence.get_violation_timeline(violation['id'])
            violation['state'] = timeline['state'] if timeline else 'OPEN'
            violation['ack_count'] = timeline['ack_count'] if timeline else 0
            enriched.append(violation)
        
        return {
            "ok": True,
            "violations": enriched,
            "count": len(enriched)
        }
    
    except Exception as e:
        logger.error(f"Failed to get active violations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_violation_history(
    station: Optional[str] = None,
    profile: Optional[str] = None,
    limit: int = 100
):
    """
    Get violation history (resolved violations).
    
    Args:
        station: Optional filter by station
        profile: Optional filter by profile
        limit: Maximum number of records
    
    Returns:
        List of historical violations
    """
    try:
        persistence = get_violation_persistence()
        
        violations = persistence.get_violation_history(
            station=station,
            profile=profile,
            limit=limit
        )
        
        return {
            "ok": True,
            "violations": violations,
            "count": len(violations)
        }
    
    except Exception as e:
        logger.error(f"Failed to get violation history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for violations service."""
    return {
        "ok": True,
        "service": "violations",
        "sprint": "Sprint 4 Extension — Violation Lifecycle & Acknowledgment",
        "capabilities": [
            "acknowledge_violations",
            "justify_violations",
            "resolve_violations",
            "timeline_tracking",
            "audit_trail"
        ]
    }
