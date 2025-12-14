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
