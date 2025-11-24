"""
SQL KPI Tool - Read-only whitelisted queries for MES data
Provides safe access to production KPIs: OEE, FPY, MTTR, downtime analysis
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import psycopg
from psycopg.rows import dict_row

def get_kpi_connection():
    """Get read-only connection to PostgreSQL KPI database"""
    host = os.getenv("POSTGRES_REPLICA_HOST", "postgres")
    port = os.getenv("POSTGRES_REPLICA_PORT", "5432")
    db = os.getenv("POSTGRES_REPLICA_DB", "ragdb")
    user = os.getenv("POSTGRES_REPLICA_USER", "postgres")
    password = os.getenv("POSTGRES_REPLICA_PASSWORD", "postgres")
    
    return psycopg.connect(
        f"host={host} port={port} dbname={db} user={user} password={password}",
        row_factory=dict_row
    )


def get_oee_metrics(
    line: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get OEE (Overall Equipment Effectiveness) metrics.
    OEE = Availability × Performance × Quality
    
    Args:
        line: Production line filter (e.g., "A01")
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
    """
    query = """
        SELECT 
            line,
            shift_date,
            shift,
            availability,
            performance,
            quality,
            oee,
            planned_production_time,
            actual_runtime,
            ideal_cycle_time,
            total_pieces,
            good_pieces
        FROM kpi_oee
        WHERE 1=1
    """
    
    params = []
    if line:
        query += " AND line = %s"
        params.append(line)
    if start_date:
        query += " AND shift_date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND shift_date <= %s"
        params.append(end_date)
    
    query += " ORDER BY shift_date DESC, shift LIMIT 100"
    
    with get_kpi_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_fpy_metrics(
    line: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get FPY (First Pass Yield) metrics.
    FPY = Good Units / Total Units (first time through)
    
    Args:
        line: Production line filter
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
    """
    query = """
        SELECT 
            line,
            shift_date,
            shift,
            total_units,
            first_pass_units,
            fpy,
            defect_count,
            rework_count,
            scrap_count
        FROM kpi_fpy
        WHERE 1=1
    """
    
    params = []
    if line:
        query += " AND line = %s"
        params.append(line)
    if start_date:
        query += " AND shift_date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND shift_date <= %s"
        params.append(end_date)
    
    query += " ORDER BY shift_date DESC, shift LIMIT 100"
    
    with get_kpi_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_mttr_metrics(
    line: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get MTTR (Mean Time To Repair) metrics.
    MTTR = Total Downtime / Number of Failures
    
    Args:
        line: Production line filter
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
    """
    query = """
        SELECT 
            line,
            shift_date,
            shift,
            total_downtime_minutes,
            failure_count,
            mttr_minutes,
            longest_downtime_minutes,
            shortest_downtime_minutes
        FROM kpi_mttr
        WHERE 1=1
    """
    
    params = []
    if line:
        query += " AND line = %s"
        params.append(line)
    if start_date:
        query += " AND shift_date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND shift_date <= %s"
        params.append(end_date)
    
    query += " ORDER BY shift_date DESC, shift LIMIT 100"
    
    with get_kpi_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_downtime_events(
    line: Optional[str] = None,
    start_date: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get recent downtime events with reasons.
    
    Args:
        line: Production line filter
        start_date: Start date (ISO format)
        limit: Maximum number of events to return
    """
    query = """
        SELECT 
            id,
            line,
            station,
            event_start,
            event_end,
            duration_minutes,
            reason_code,
            reason_description,
            operator_notes
        FROM downtime_events
        WHERE 1=1
    """
    
    params = []
    if line:
        query += " AND line = %s"
        params.append(line)
    if start_date:
        query += " AND event_start >= %s"
        params.append(start_date)
    
    query += f" ORDER BY event_start DESC LIMIT {min(limit, 200)}"
    
    with get_kpi_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_line_summary(line: str, days: int = 7) -> Dict[str, Any]:
    """
    Get comprehensive summary for a production line.
    
    Args:
        line: Production line (e.g., "A01")
        days: Number of days to look back
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    oee_data = get_oee_metrics(line, str(start_date), str(end_date))
    fpy_data = get_fpy_metrics(line, str(start_date), str(end_date))
    mttr_data = get_mttr_metrics(line, str(start_date), str(end_date))
    
    # Calculate averages
    avg_oee = sum(r['oee'] for r in oee_data) / len(oee_data) if oee_data else 0
    avg_fpy = sum(r['fpy'] for r in fpy_data) / len(fpy_data) if fpy_data else 0
    avg_mttr = sum(r['mttr_minutes'] for r in mttr_data) / len(mttr_data) if mttr_data else 0
    
    return {
        "line": line,
        "period_days": days,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "avg_oee": round(avg_oee, 2),
        "avg_fpy": round(avg_fpy, 2),
        "avg_mttr_minutes": round(avg_mttr, 2),
        "data_points": {
            "oee": len(oee_data),
            "fpy": len(fpy_data),
            "mttr": len(mttr_data)
        },
        "latest_oee": oee_data[0] if oee_data else None,
        "latest_fpy": fpy_data[0] if fpy_data else None,
        "latest_mttr": mttr_data[0] if mttr_data else None
    }


def check_kpi_health() -> Dict[str, Any]:
    """Check if KPI database connection is working"""
    try:
        with get_kpi_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM kpi_oee")
                result = cur.fetchone()
                return {
                    "available": True,
                    "oee_records": result['count'] if result else 0
                }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }
