from fastapi import APIRouter, Query
from typing import Optional
from packages.tools.sqlkpi import (
    get_oee_metrics,
    get_fpy_metrics,
    get_mttr_metrics,
    get_downtime_events,
    get_line_summary,
    check_kpi_health
)

router = APIRouter(tags=["kpi"])

@router.get("/kpi/oee")
def kpi_oee(
    line: Optional[str] = Query(None, description="Production line (e.g., A01)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get OEE (Overall Equipment Effectiveness) metrics"""
    return {
        "metrics": get_oee_metrics(line, start_date, end_date),
        "filters": {"line": line, "start_date": start_date, "end_date": end_date}
    }

@router.get("/kpi/fpy")
def kpi_fpy(
    line: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get FPY (First Pass Yield) metrics"""
    return {
        "metrics": get_fpy_metrics(line, start_date, end_date),
        "filters": {"line": line, "start_date": start_date, "end_date": end_date}
    }

@router.get("/kpi/mttr")
def kpi_mttr(
    line: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get MTTR (Mean Time To Repair) metrics"""
    return {
        "metrics": get_mttr_metrics(line, start_date, end_date),
        "filters": {"line": line, "start_date": start_date, "end_date": end_date}
    }

@router.get("/kpi/downtime")
def kpi_downtime(
    line: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """Get recent downtime events"""
    return {
        "events": get_downtime_events(line, start_date, limit),
        "filters": {"line": line, "start_date": start_date}
    }

@router.get("/kpi/summary/{line}")
def kpi_summary(
    line: str,
    days: int = Query(7, ge=1, le=30, description="Number of days to look back")
):
    """Get comprehensive KPI summary for a production line"""
    return get_line_summary(line, days)

@router.get("/health/kpi")
def kpi_health_check():
    """Check KPI database connectivity"""
    return check_kpi_health()
