"""
OEE SQL Tool - Allows LLM to query OEE data using natural language
"""
from sqlalchemy import create_engine, text
import os
from typing import Dict, Any, Optional

def get_db_engine():
    """Create SQLAlchemy engine for PostgreSQL"""
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "mes_db")
    DB_USER = os.getenv("POSTGRES_USER", "mes_user")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "mes_pass")
    
    connection_string = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(connection_string)

def query_oee_trend(
    line_id: str,
    days: int = 14,
    shift: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query OEE trend data for a specific line.
    
    Args:
        line_id: Line identifier (e.g., 'M10', 'A01', 'C03')
        days: Number of days to look back (default 14)
        shift: Optional shift filter ('M', 'A', 'N')
    
    Returns:
        Dictionary with trend data and top losses
    """
    engine = get_db_engine()
    
    shift_filter = ""
    if shift:
        shift_filter = f"AND shift = '{shift}'"
    
    with engine.begin() as conn:
        # Get trend data
        query = text(f"""
            SELECT 
                date,
                shift,
                line_name,
                ROUND(availability::numeric, 3) as availability,
                ROUND(performance::numeric, 3) as performance,
                ROUND(quality::numeric, 3) as quality,
                ROUND(oee::numeric, 3) as oee,
                unplanned_downtime_min,
                total_units_produced,
                good_units,
                scrap_units,
                main_loss_category
            FROM oee_line_shift
            WHERE line_id = :line_id
              AND date >= CURRENT_DATE - INTERVAL '{days} days'
              {shift_filter}
            ORDER BY date DESC, shift
        """)
        
        result = conn.execute(query, {"line_id": line_id})
        rows = result.fetchall()
        
        if not rows:
            return {"error": f"No data found for line {line_id}"}
        
        # Get top losses
        loss_query = text(f"""
            SELECT 
                main_loss_category,
                COUNT(*) as occurrences,
                ROUND(SUM(unplanned_downtime_min)::numeric, 1) as total_downtime_min
            FROM oee_line_shift
            WHERE line_id = :line_id
              AND date >= CURRENT_DATE - INTERVAL '{days} days'
              {shift_filter}
            GROUP BY main_loss_category
            ORDER BY total_downtime_min DESC
            LIMIT 5
        """)
        
        loss_result = conn.execute(loss_query, {"line_id": line_id})
        losses = loss_result.fetchall()
        
        # Calculate averages
        avg_oee = sum(float(r.oee) for r in rows) / len(rows)
        avg_availability = sum(float(r.availability) for r in rows) / len(rows)
        avg_performance = sum(float(r.performance) for r in rows) / len(rows)
        avg_quality = sum(float(r.quality) for r in rows) / len(rows)
        total_downtime = sum(float(r.unplanned_downtime_min) for r in rows)
        
        return {
            "line_id": line_id,
            "line_name": rows[0].line_name,
            "period": f"Last {days} days",
            "shift_filter": shift if shift else "All shifts",
            "records": len(rows),
            "averages": {
                "oee": round(avg_oee, 3),
                "availability": round(avg_availability, 3),
                "performance": round(avg_performance, 3),
                "quality": round(avg_quality, 3),
                "total_downtime_min": round(total_downtime, 1)
            },
            "top_losses": [
                {
                    "category": r.main_loss_category,
                    "occurrences": int(r.occurrences),
                    "downtime_min": float(r.total_downtime_min)
                }
                for r in losses
            ],
            "recent_data": [
                {
                    "date": str(r.date),
                    "shift": r.shift,
                    "oee": float(r.oee),
                    "availability": float(r.availability),
                    "performance": float(r.performance),
                    "quality": float(r.quality),
                    "main_loss": r.main_loss_category
                }
                for r in rows[:7]  # Last 7 records
            ]
        }

OEE_TOOL_DESCRIPTION = """
Available tool: query_oee_trend(line_id, days=14, shift=None)

This tool queries OEE (Overall Equipment Effectiveness) data from the PostgreSQL database.

Parameters:
- line_id: Line identifier (e.g., 'M10', 'A01', 'C03', 'D01')
- days: Number of days to analyze (default 14)
- shift: Optional shift filter ('M'=Morning, 'A'=Afternoon, 'N'=Night)

Returns:
- Average OEE, Availability, Performance, Quality metrics
- Top loss categories with downtime minutes
- Recent trend data by shift

Example usage in your answer:
"Let me check the OEE data for Line M10..."
[Use query_oee_trend('M10', 14, None)]
"Based on the data, Line M10 has an average OEE of X% over the last 14 days..."
"""

def get_oee_tool_prompt() -> str:
    """Get the prompt to include OEE tool capabilities"""
    return OEE_TOOL_DESCRIPTION
