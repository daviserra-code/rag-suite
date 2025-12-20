"""
OEE Analytics Router - SQL-based OEE trend analysis
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import create_engine, text
import os

router = APIRouter(tags=["oee"])

def get_db_engine():
    """Create SQLAlchemy engine for PostgreSQL"""
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "mes_db")
    DB_USER = os.getenv("POSTGRES_USER", "mes_user")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "mes_pass")
    
    connection_string = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Connection pooling configuration
    pool_size = int(os.getenv("SQLALCHEMY_POOL_SIZE", "10"))
    max_overflow = int(os.getenv("SQLALCHEMY_MAX_OVERFLOW", "20"))
    pool_recycle = int(os.getenv("SQLALCHEMY_POOL_RECYCLE", "3600"))
    pool_pre_ping = os.getenv("SQLALCHEMY_POOL_PRE_PING", "true").lower() == "true"
    
    return create_engine(
        connection_string,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle,
        pool_pre_ping=pool_pre_ping
    )

class OEETrendRequest(BaseModel):
    line_id: str
    days: int = 14
    shift: Optional[str] = None  # If None, show all shifts

@router.post("/oee/trend")
def get_oee_trend(req: OEETrendRequest):
    """
    Get OEE trend for a specific line over the last N days
    Returns: trend data + top loss categories
    """
    engine = get_db_engine()
    
    try:
        with engine.begin() as conn:
            # Build query with optional shift filter
            shift_filter = ""
            if req.shift:
                shift_filter = f"AND shift = '{req.shift}'"
            
            # Get OEE trend - use most recent N days of data available
            query = text(f"""
                WITH recent_data AS (
                    SELECT 
                        date,
                        shift,
                        line_name,
                        ROUND(availability::numeric, 4) as availability,
                        ROUND(performance::numeric, 4) as performance,
                        ROUND(quality::numeric, 4) as quality,
                        ROUND(oee::numeric, 4) as oee,
                        planned_time_min,
                        unplanned_downtime_min,
                        total_units_produced,
                        good_units,
                        scrap_units,
                        main_loss_category,
                        ROW_NUMBER() OVER (ORDER BY date DESC, shift) as rn
                    FROM oee_line_shift
                    WHERE line_id = :line_id
                      {shift_filter}
                )
                SELECT * FROM recent_data
                WHERE rn <= :limit
                ORDER BY date DESC, shift
            """)
            
            result = conn.execute(query, {"line_id": req.line_id, "limit": req.days * 3})
            rows = result.fetchall()
            
            if not rows:
                raise HTTPException(status_code=404, detail=f"No data found for line {req.line_id}")
            
            # Convert to list of dicts
            trend_data = []
            for row in rows:
                trend_data.append({
                    "date": str(row.date),
                    "shift": row.shift,
                    "line_name": row.line_name,
                    "availability": float(row.availability),
                    "performance": float(row.performance),
                    "quality": float(row.quality),
                    "oee": float(row.oee),
                    "planned_time_min": float(row.planned_time_min) if row.planned_time_min else 0,
                    "downtime_min": float(row.unplanned_downtime_min) if row.unplanned_downtime_min else 0,
                    "total_units": int(row.total_units_produced) if row.total_units_produced else 0,
                    "good_units": int(row.good_units) if row.good_units else 0,
                    "scrap_units": int(row.scrap_units) if row.scrap_units else 0,
                    "main_loss": row.main_loss_category
                })
            
            # Get top loss categories from same dataset
            loss_query = text(f"""
                WITH recent_data AS (
                    SELECT 
                        main_loss_category,
                        unplanned_downtime_min,
                        oee,
                        ROW_NUMBER() OVER (ORDER BY date DESC, shift) as rn
                    FROM oee_line_shift
                    WHERE line_id = :line_id
                      {shift_filter}
                )
                SELECT 
                    main_loss_category,
                    COUNT(*) as occurrences,
                    ROUND(SUM(unplanned_downtime_min)::numeric, 1) as total_downtime_min,
                    ROUND(AVG(oee)::numeric, 4) as avg_oee
                FROM recent_data
                WHERE rn <= :limit
                GROUP BY main_loss_category
                ORDER BY total_downtime_min DESC
                LIMIT 5
            """)
            
            loss_result = conn.execute(loss_query, {"line_id": req.line_id, "limit": req.days * 3})
            top_losses = []
            for row in loss_result:
                top_losses.append({
                    "category": row.main_loss_category,
                    "occurrences": int(row.occurrences),
                    "total_downtime_min": float(row.total_downtime_min),
                    "avg_oee": float(row.avg_oee)
                })
            
            # Calculate summary statistics
            avg_oee = sum(d["oee"] for d in trend_data) / len(trend_data)
            avg_availability = sum(d["availability"] for d in trend_data) / len(trend_data)
            avg_performance = sum(d["performance"] for d in trend_data) / len(trend_data)
            avg_quality = sum(d["quality"] for d in trend_data) / len(trend_data)
            
            return {
                "line_id": req.line_id,
                "line_name": trend_data[0]["line_name"],
                "period_days": req.days,
                "shift_filter": req.shift,
                "records": len(trend_data),
                "summary": {
                    "avg_oee": round(avg_oee, 4),
                    "avg_availability": round(avg_availability, 4),
                    "avg_performance": round(avg_performance, 4),
                    "avg_quality": round(avg_quality, 4)
                },
                "trend_data": trend_data,
                "top_losses": top_losses
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/oee/lines")
def list_lines():
    """List all available lines with OEE data"""
    engine = get_db_engine()
    
    try:
        with engine.begin() as conn:
            query = text("""
                SELECT 
                    line_id,
                    line_name,
                    COUNT(*) as shifts,
                    MIN(date) as start_date,
                    MAX(date) as end_date,
                    ROUND(AVG(oee)::numeric, 4) as avg_oee,
                    ROUND(AVG(availability)::numeric, 4) as avg_availability,
                    ROUND(AVG(performance)::numeric, 4) as avg_performance,
                    ROUND(AVG(quality)::numeric, 4) as avg_quality
                FROM oee_line_shift
                GROUP BY line_id, line_name
                ORDER BY avg_oee DESC
            """)
            
            result = conn.execute(query)
            lines = []
            for row in result:
                lines.append({
                    "line_id": row.line_id,
                    "line_name": row.line_name,
                    "shifts": int(row.shifts),
                    "start_date": str(row.start_date),
                    "end_date": str(row.end_date),
                    "avg_oee": float(row.avg_oee),
                    "avg_availability": float(row.avg_availability),
                    "avg_performance": float(row.avg_performance),
                    "avg_quality": float(row.avg_quality)
                })
            
            return lines
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
