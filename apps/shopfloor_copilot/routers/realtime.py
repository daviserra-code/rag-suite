"""
Real-Time Data Streaming API
WebSocket endpoint for live OEE updates and alerts
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import asyncio
import json
from datetime import datetime
from sqlalchemy import text
from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine

router = APIRouter()

# Store active WebSocket connections
active_connections: List[WebSocket] = []


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


manager = ConnectionManager()


async def monitor_live_data():
    """Background task to monitor and broadcast live data updates"""
    engine = get_db_engine()
    last_check_time = datetime.now()
    
    while True:
        try:
            if len(manager.active_connections) > 0:
                with engine.connect() as conn:
                    # Get latest OEE data for all lines
                    result = conn.execute(text("""
                        SELECT 
                            line_id, line_name,
                            oee, availability, performance, quality,
                            total_units_produced, good_units,
                            date, shift
                        FROM oee_line_shift
                        WHERE date = CURRENT_DATE
                        ORDER BY line_id
                    """))
                    
                    lines_data = [dict(row._mapping) for row in result]
                    
                    # Get active maintenance alerts
                    alerts_result = conn.execute(text("""
                        SELECT 
                            alert_id, line_id, equipment_name,
                            severity, predicted_failure_date
                        FROM maintenance_alerts
                        WHERE current_status = 'active'
                        ORDER BY severity DESC
                        LIMIT 5
                    """))
                    
                    alerts = [dict(row._mapping) for row in alerts_result]
                    
                    # Prepare update message
                    update_message = {
                        "type": "live_update",
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "lines": lines_data,
                            "alerts": alerts,
                            "summary": {
                                "total_lines": len(lines_data),
                                "avg_oee": sum(l['oee'] for l in lines_data) / len(lines_data) if lines_data else 0,
                                "active_alerts": len(alerts)
                            }
                        }
                    }
                    
                    # Broadcast to all connected clients
                    await manager.broadcast(update_message)
                
                last_check_time = datetime.now()
            
        except Exception as e:
            print(f"Error in live monitoring: {e}")
        
        # Wait 5 seconds before next update
        await asyncio.sleep(5)


@router.get("/runtime/snapshot")
async def get_runtime_snapshot():
    """
    Runtime Snapshot Proxy (Phase A - Task 1)
    
    Fetches live plant state from OPC Studio if available,
    otherwise falls back to simulation DB.
    
    Returns unified structure for AI context injection.
    """
    import os
    import time
    from datetime import datetime, timedelta
    
    opc_url = os.getenv("OPC_STUDIO_URL", "http://opc-studio:8040")
    max_age_s = int(os.getenv("RUNTIME_MAX_AGE_S", "30"))
    runtime_source = os.getenv("RUNTIME_SOURCE", "auto")
    
    opc_snapshot = None
    opc_timestamp = None
    source = "simulation"
    
    # Try to fetch from OPC Studio if enabled
    if runtime_source in ("opc", "auto"):
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{opc_url}/snapshot")
                if response.status_code == 200:
                    opc_data = response.json()
                    if opc_data.get("ok"):
                        opc_snapshot = opc_data.get("data", {})
                        opc_timestamp = datetime.now()
                        source = "opc"
        except Exception as e:
            print(f"OPC Studio unavailable: {e}")
    
    # Check if OPC data is fresh
    if opc_snapshot and opc_timestamp:
        age = (datetime.now() - opc_timestamp).total_seconds()
        if age > max_age_s:
            print(f"OPC data stale ({age}s > {max_age_s}s), falling back to simulation")
            opc_snapshot = None
            source = "simulation"
    
    # Use OPC data if available and fresh
    if opc_snapshot:
        return {
            "ok": True,
            "source": source,
            "timestamp": opc_timestamp.isoformat() if opc_timestamp else None,
            "data": opc_snapshot
        }
    
    # Fallback: query simulation DB (read-only)
    engine = get_db_engine()
    with engine.connect() as conn:
        # Get latest shift data for all lines
        lines_result = conn.execute(text("""
            SELECT DISTINCT ON (line_id)
                line_id,
                line_name,
                oee,
                availability,
                performance,
                quality,
                date,
                shift
            FROM oee_line_shift
            WHERE date >= CURRENT_DATE - INTERVAL '1 day'
            ORDER BY line_id, date DESC, shift DESC
        """))
        
        lines_data = {}
        for row in lines_result:
            line_id = row.line_id
            lines_data[line_id] = {
                "status": "RUNNING",
                "oee": float(row.oee or 0),
                "availability": float(row.availability or 0),
                "performance": float(row.performance or 0),
                "quality": float(row.quality or 0),
                "stations": {}
            }
        
        # Get station data if available
        try:
            stations_result = conn.execute(text("""
                SELECT 
                    line_id,
                    station_id,
                    status,
                    uptime_percentage
                FROM station_realtime
                WHERE last_update >= NOW() - INTERVAL '1 hour'
            """))
            
            for row in stations_result:
                line_id = row.line_id
                if line_id in lines_data:
                    lines_data[line_id]["stations"][row.station_id] = {
                        "state": row.status or "RUNNING",
                        "cycle_time_s": 0.0,
                        "good_count": 0,
                        "scrap_count": 0,
                        "alarms": []
                    }
        except Exception as e:
            print(f"Station data not available: {e}")
    
    return {
        "ok": True,
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "data": {
            "plant": "SIMULATION",
            "lines": lines_data
        }
    }


@router.get("/runtime/snapshot")
async def get_runtime_snapshot():
    """
    Runtime Snapshot Proxy - Phase A implementation
    
    Fetches live plant state from OPC Studio if available,
    otherwise falls back to simulation DB.
    
    Returns unified structure with source indicator.
    """
    import os
    import httpx
    from datetime import datetime, timedelta
    
    # Configuration
    opc_url = os.getenv("OPC_STUDIO_URL", "http://opc-studio:8040")
    runtime_source = os.getenv("RUNTIME_SOURCE", "auto")  # opc|sim|auto
    max_age_seconds = int(os.getenv("RUNTIME_MAX_AGE_S", "30"))
    
    snapshot_data = None
    source = "unknown"
    timestamp = None
    error_message = None
    
    # Try OPC Studio first if source is 'opc' or 'auto'
    if runtime_source in ("opc", "auto"):
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{opc_url}/snapshot")
                if response.status_code == 200:
                    opc_snapshot = response.json()
                    
                    # Check if data is fresh enough
                    if opc_snapshot.get("ok"):
                        snapshot_data = opc_snapshot.get("data", {})
                        source = "opc-studio"
                        timestamp = datetime.now().isoformat()
                        
        except Exception as e:
            error_message = f"OPC Studio unavailable: {str(e)}"
            if runtime_source == "opc":
                # If explicitly requested OPC only, return error
                return {
                    "ok": False,
                    "error": error_message,
                    "source": "opc-studio-failed"
                }
    
    # Fallback to simulation DB if OPC failed or source is 'sim'
    if snapshot_data is None or runtime_source == "sim":
        try:
            engine = get_db_engine()
            with engine.begin() as conn:
                # Get latest OEE metrics from simulation
                result = conn.execute(text("""
                    SELECT 
                        line_id,
                        line_name,
                        AVG(oee) as oee,
                        AVG(availability) as availability,
                        AVG(performance) as performance,
                        AVG(quality) as quality,
                        'SIMULATED' as status
                    FROM oee_line_shift
                    WHERE date >= CURRENT_DATE - INTERVAL '1 day'
                    GROUP BY line_id, line_name
                """))
                
                lines = {}
                for row in result:
                    lines[row.line_id] = {
                        "status": row.status,
                        "oee": float(row.oee or 0),
                        "availability": float(row.availability or 0),
                        "performance": float(row.performance or 0),
                        "quality": float(row.quality or 0),
                        "stations": {}  # Simulation doesn't have station-level detail
                    }
                
                snapshot_data = {
                    "plant": "SHOPFLOOR-SIMULATION",
                    "lines": lines
                }
                source = "simulation-db"
                timestamp = datetime.now().isoformat()
                
        except Exception as e:
            return {
                "ok": False,
                "error": f"Failed to fetch from both OPC Studio and simulation DB: {str(e)}",
                "source": "all-failed"
            }
    
    # Return unified response
    return {
        "ok": True,
        "source": source,
        "timestamp": timestamp,
        "data": snapshot_data,
        "fallback_used": source == "simulation-db",
        "opc_error": error_message
    }


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming"""
    await manager.connect(websocket)
    
    # Send initial connection confirmation
    await manager.send_personal_message({
        "type": "connection",
        "status": "connected",
        "message": "Connected to live data stream",
        "timestamp": datetime.now().isoformat()
    }, websocket)
    
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            
            # Echo back or handle client commands
            if data == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.on_event("startup")
async def startup_event():
    """Start background monitoring task"""
    asyncio.create_task(monitor_live_data())
    print("🚀 Real-time monitoring service started")
