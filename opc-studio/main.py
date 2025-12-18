"""
OPC Studio - Digital Twin Gateway for Shopfloor-Copilot
Bridges OT Systems, MES, and AI through OPC UA
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from asyncua import Server, ua

from opc_server import OPCUAServerManager
from historian_bridge import HistorianBridge
from scenario_engine import ScenarioEngine
from plant_model import PlantModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
opc_server_manager: Optional[OPCUAServerManager] = None
historian_bridge: Optional[HistorianBridge] = None
scenario_engine: Optional[ScenarioEngine] = None
plant_model: Optional[PlantModel] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global opc_server_manager, historian_bridge, scenario_engine, plant_model
    
    logger.info("🚀 Starting OPC Studio...")
    
    # Initialize plant model
    plant_model = PlantModel()
    await plant_model.load_model()
    logger.info(f"✅ Loaded plant model with {len(plant_model.production_lines)} production lines")
    
    # Initialize OPC UA server
    opc_server_manager = OPCUAServerManager(plant_model=plant_model)
    await opc_server_manager.start()
    logger.info("✅ OPC UA server started on port 4840")
    
    # Initialize historian bridge
    historian_bridge = HistorianBridge(opc_server=opc_server_manager)
    await historian_bridge.start()
    logger.info("✅ Historian bridge started")
    
    # Initialize scenario engine
    scenario_engine = ScenarioEngine(opc_server=opc_server_manager, plant_model=plant_model)
    logger.info("✅ Scenario engine initialized")
    
    logger.info("🎉 OPC Studio is ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down OPC Studio...")
    if historian_bridge:
        await historian_bridge.stop()
    if opc_server_manager:
        await opc_server_manager.stop()
    logger.info("✅ OPC Studio shutdown complete")


app = FastAPI(
    title="OPC Studio API",
    description="Digital Twin Gateway for Shopfloor-Copilot",
    version="1.0.0",
    lifespan=lifespan
)


# ==================== Health & Status ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "opc_server": opc_server_manager is not None and opc_server_manager.is_running(),
            "historian_bridge": historian_bridge is not None and historian_bridge.is_running(),
            "scenario_engine": scenario_engine is not None
        }
    }


@app.get("/api/status")
async def get_status():
    """Get detailed status of all OPC Studio components"""
    if not opc_server_manager:
        raise HTTPException(status_code=503, detail="OPC server not initialized")
    
    return {
        "opc_server": {
            "running": opc_server_manager.is_running(),
            "endpoint": f"opc.tcp://localhost:4840/opcua",
            "namespace": "http://shopfloor-copilot.local",
            "nodes_count": opc_server_manager.get_nodes_count()
        },
        "historian": {
            "running": historian_bridge.is_running() if historian_bridge else False,
            "sync_interval_seconds": 30,
            "last_sync": historian_bridge.get_last_sync_time() if historian_bridge else None
        },
        "scenario_engine": {
            "active": scenario_engine is not None,
            "active_scenarios": scenario_engine.get_active_scenarios() if scenario_engine else []
        },
        "plant_model": {
            "production_lines": len(plant_model.production_lines) if plant_model else 0,
            "total_stations": sum(len(line.stations) for line in plant_model.production_lines) if plant_model else 0
        }
    }


# ==================== Plant Model API ====================

@app.get("/api/plant-model")
async def get_plant_model():
    """Get the complete plant model structure"""
    if not plant_model:
        raise HTTPException(status_code=503, detail="Plant model not loaded")
    
    return plant_model.to_dict()


@app.get("/api/plant-model/lines")
async def get_production_lines():
    """Get all production lines"""
    if not plant_model:
        raise HTTPException(status_code=503, detail="Plant model not loaded")
    
    return [line.to_dict() for line in plant_model.production_lines]


@app.get("/api/plant-model/lines/{line_id}")
async def get_production_line(line_id: str):
    """Get a specific production line"""
    if not plant_model:
        raise HTTPException(status_code=503, detail="Plant model not loaded")
    
    line = plant_model.get_line(line_id)
    if not line:
        raise HTTPException(status_code=404, detail=f"Line {line_id} not found")
    
    return line.to_dict()


# ==================== OPC UA Browser API ====================

@app.get("/api/opc/browse")
async def browse_opc_nodes(node_id: Optional[str] = None):
    """Browse OPC UA namespace"""
    if not opc_server_manager:
        raise HTTPException(status_code=503, detail="OPC server not initialized")
    
    try:
        nodes = await opc_server_manager.browse_nodes(node_id)
        return {"nodes": nodes}
    except Exception as e:
        logger.error(f"Error browsing OPC nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/opc/read/{node_path}")
async def read_opc_node(node_path: str):
    """Read value from OPC UA node"""
    if not opc_server_manager:
        raise HTTPException(status_code=503, detail="OPC server not initialized")
    
    try:
        value = await opc_server_manager.read_node(node_path)
        return {
            "node_path": node_path,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error reading OPC node: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Scenario Engine API ====================

class ScenarioRequest(BaseModel):
    scenario_type: str  # MaterialShortage, EquipmentFailure, QualityIssue, etc.
    target_line: str
    target_station: Optional[str] = None
    duration_minutes: int = 30
    severity: str = "medium"  # low, medium, high
    parameters: dict = {}


@app.post("/api/scenarios/inject")
async def inject_scenario(request: ScenarioRequest):
    """Inject a what-if scenario into the plant simulation"""
    if not scenario_engine:
        raise HTTPException(status_code=503, detail="Scenario engine not initialized")
    
    try:
        scenario_id = await scenario_engine.inject_scenario(
            scenario_type=request.scenario_type,
            target_line=request.target_line,
            target_station=request.target_station,
            duration_minutes=request.duration_minutes,
            severity=request.severity,
            parameters=request.parameters
        )
        
        return {
            "scenario_id": scenario_id,
            "message": f"Scenario {request.scenario_type} injected successfully",
            "status": "active"
        }
    except Exception as e:
        logger.error(f"Error injecting scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scenarios/active")
async def get_active_scenarios():
    """Get all active scenarios"""
    if not scenario_engine:
        raise HTTPException(status_code=503, detail="Scenario engine not initialized")
    
    return {
        "active_scenarios": scenario_engine.get_active_scenarios(),
        "count": len(scenario_engine.get_active_scenarios())
    }


@app.delete("/api/scenarios/{scenario_id}")
async def stop_scenario(scenario_id: str):
    """Stop an active scenario"""
    if not scenario_engine:
        raise HTTPException(status_code=503, detail="Scenario engine not initialized")
    
    try:
        await scenario_engine.stop_scenario(scenario_id)
        return {
            "scenario_id": scenario_id,
            "message": "Scenario stopped successfully"
        }
    except Exception as e:
        logger.error(f"Error stopping scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Historian Bridge API ====================

@app.post("/api/historian/sync")
async def trigger_sync():
    """Manually trigger historian sync"""
    if not historian_bridge:
        raise HTTPException(status_code=503, detail="Historian bridge not initialized")
    
    try:
        await historian_bridge.sync_to_database()
        return {
            "message": "Sync completed successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error during sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/historian/stats")
async def get_historian_stats():
    """Get historian bridge statistics"""
    if not historian_bridge:
        raise HTTPException(status_code=503, detail="Historian bridge not initialized")
    
    return historian_bridge.get_stats()


if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("OPC_STUDIO_HTTP_PORT", "8040"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
