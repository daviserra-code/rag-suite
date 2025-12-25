from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Any, List, Dict
from .state import PlantState
from .historian import Historian
from .scenario_engine import get_scenario_engine
from .opcua_client import get_client
from .semantic_engine import get_semantic_engine

def build_api(state: PlantState, historian: Historian) -> FastAPI:
    app = FastAPI(title="OPC Studio API", version="0.4.0")
    
    # Load engines and clients
    scenario_engine = get_scenario_engine()
    opcua_client = get_client()
    semantic_engine = get_semantic_engine()

    class ScenarioReq(BaseModel):
        line: str = "A01"
        station: str = "ST17"
        event: str = "MaterialShortage"
        duration_min: float = 15
        impact: dict | None = None
        template_id: Optional[str] = None
        severity: Optional[str] = None

    @app.get("/health")
    def health():
        return {"ok": True, "service": "opc-studio", "version": "0.2.1"}

    @app.get("/model")
    def model():
        return {"ok": True, "model": state.list_model()}

    @app.get("/snapshot")
    def snapshot():
        return state.snapshot()
    
    @app.get("/semantic/snapshot")
    def semantic_snapshot(station: str = None):
        """
        Get semantic snapshot with material context.
        
        If station is specified, returns focused view for that station.
        Otherwise returns full plant snapshot.
        
        Material context is always included for each station, with evidence_present flag.
        """
        # Import at runtime to avoid circular dependencies
        import os
        import psycopg
        
        def fetch_material_context(station_id: str) -> dict:
            """Fetch material context from v_material_evidence"""
            try:
                db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/ragdb")
                with psycopg.connect(db_url) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT 
                                mode, active_serial, active_lot, 
                                work_order, operation,
                                bom_revision, as_built_revision,
                                quality_status,
                                dry_run_authorization,
                                deviation_id,
                                tooling_calibration_ok,
                                operator_certified,
                                material_ts
                            FROM v_material_evidence
                            WHERE station = %s
                            LIMIT 1
                            """,
                            (station_id,)
                        )
                        
                        row = cur.fetchone()
                        
                        if row:
                            return {
                                "mode": row[0],
                                "active_serial": row[1],
                                "active_lot": row[2],
                                "work_order": row[3],
                                "operation": row[4],
                                "bom_revision": row[5],
                                "as_built_revision": row[6],
                                "quality_status": row[7],
                                "dry_run_authorization": row[8],
                                "deviation_id": row[9],
                                "tooling_calibration_ok": row[10],
                                "operator_certified": row[11],
                                "material_ts": row[12].isoformat() if row[12] else None,
                                "evidence_present": True
                            }
                        else:
                            # No evidence - return default
                            return {
                                "mode": None,
                                "active_serial": None,
                                "active_lot": None,
                                "work_order": None,
                                "operation": None,
                                "bom_revision": None,
                                "as_built_revision": None,
                                "quality_status": None,
                                "dry_run_authorization": None,
                                "deviation_id": None,
                                "tooling_calibration_ok": None,
                                "operator_certified": None,
                                "material_ts": None,
                                "evidence_present": False
                            }
            except Exception as e:
                return {
                    "mode": None,
                    "active_serial": None,
                    "active_lot": None,
                    "work_order": None,
                    "operation": None,
                    "bom_revision": None,
                    "as_built_revision": None,
                    "quality_status": None,
                    "dry_run_authorization": None,
                    "deviation_id": None,
                    "tooling_calibration_ok": None,
                    "operator_certified": None,
                    "material_ts": None,
                    "evidence_present": False,
                    "error": str(e)
                }
        
        # Get base snapshot
        base_snapshot = state.snapshot()
        
        # If specific station requested
        if station:
            # Find the station
            lines = base_snapshot.get('data', {}).get('lines', {})
            for line_id, line_data in lines.items():
                stations = line_data.get('stations', {})
                if station in stations:
                    # Fetch material context
                    material_context = fetch_material_context(station)
                    return {
                        "ok": True,
                        "station": station,
                        "line": line_id,
                        "station_data": stations[station],
                        "material_context": material_context
                    }
            
            # Station not found
            raise HTTPException(status_code=404, detail=f"Station {station} not found")
        
        # Full snapshot - add material context to all stations
        snapshot_with_material = base_snapshot.copy()
        lines = snapshot_with_material.get('data', {}).get('lines', {})
        
        for line_id, line_data in lines.items():
            stations = line_data.get('stations', {})
            for station_id in stations.keys():
                material_context = fetch_material_context(station_id)
                stations[station_id]['material_context'] = material_context
        
        return snapshot_with_material

    @app.get("/historian/status")
    def hist_status():
        return {
            "ok": True,
            "enabled": historian.enabled,
            "interval_s": historian.interval_s,
            "last_write_ts": historian.last_write_ts,
            "last_error": historian.last_error,
        }

    @app.get("/scenario/taxonomy")
    def get_taxonomy():
        """Get scenario taxonomy and severity levels"""
        return {
            "ok": True,
            "taxonomy": scenario_engine.get_taxonomy()
        }
    
    @app.get("/scenario/templates")
    def get_templates():
        """Get all scenario templates"""
        return {
            "ok": True,
            "templates": scenario_engine.get_templates()
        }
    
    @app.get("/scenario/templates/{template_id}")
    def get_template(template_id: str):
        """Get specific template by ID"""
        template = scenario_engine.get_template_by_id(template_id)
        if template:
            return {"ok": True, "template": template}
        return {"ok": False, "error": f"Template '{template_id}' not found"}

    @app.post("/scenario/apply")
    def apply_scenario(req: ScenarioReq):
        """Apply scenario with optional template-based logic"""
        
        # If template_id provided, use template-based application
        if req.template_id:
            line_key = state._resolve_line(req.line)
            station_key = state._resolve_station(line_key, req.station) if line_key else None
            
            if not line_key or not station_key:
                return {"ok": False, "error": f"Invalid line '{req.line}' or station '{req.station}'"}
            
            line_state = state.data["lines"][line_key]
            station_state = line_state["stations"][station_key]
            
            # Apply template with cascading logic
            template_result = scenario_engine.apply_template(
                req.template_id,
                line_state,
                station_state,
                req.severity
            )
            
            if "error" in template_result:
                return {"ok": False, "error": template_result["error"]}
            
            # Build impact from template
            impact = template_result["impact"]
            duration_min = template_result["duration_min"]
            alarms = template_result["alarms"]
            
            # Apply to state
            scenario_payload = {
                "line": req.line,
                "station": req.station,
                "event": template_result["template"]["name"],
                "duration_min": duration_min,
                "impact": impact,
                "template_id": req.template_id,
                "severity": template_result["severity"],
                "cascading_effects": template_result["cascading_effects"]
            }
            
            res = state.apply_scenario(scenario_payload)
            
            if res.get("ok"):
                # Add alarms from template
                station_state["alarms"].extend(alarms)
                
                # Apply cascading effects
                for cascade in template_result["cascading_effects"]:
                    for effect in cascade.get("effects", []):
                        target = effect.get("target")
                        
                        if target == "line":
                            # Apply line-level multipliers
                            if "availability_multiplier" in effect:
                                line_state["availability"] *= effect["availability_multiplier"]
                            if "performance_multiplier" in effect:
                                line_state["performance"] *= effect["performance_multiplier"]
                            if "quality_multiplier" in effect:
                                line_state["quality"] *= effect["quality_multiplier"]
                            line_state["oee"] = round(
                                line_state["availability"] * line_state["performance"] * line_state["quality"], 4
                            )
                        
                        elif target == "downstream_stations":
                            # Apply to all stations after current
                            station_keys = list(line_state["stations"].keys())
                            current_idx = station_keys.index(station_key)
                            for downstream_key in station_keys[current_idx + 1:]:
                                downstream = line_state["stations"][downstream_key]
                                if "availability_multiplier" in effect:
                                    # Reduce downstream availability
                                    downstream["cycle_time_s"] *= (2 - effect["availability_multiplier"])
                                if "state" in effect:
                                    downstream["state"] = effect["state"]
                                if "alarms" in effect:
                                    downstream["alarms"].extend(effect["alarms"])
                
                # Write to historian
                plant = state.data.get("plant", "PLANT")
                historian.write_event(plant, line_key, station_key, template_result["template"]["name"], scenario_payload)
                
                # Add template info to response
                res["template_applied"] = {
                    "id": req.template_id,
                    "name": template_result["template"]["name"],
                    "severity": template_result["severity"],
                    "cascading": len(template_result["cascading_effects"]) > 0
                }
            
            return res
        
        # Legacy scenario application (no template)
        res = state.apply_scenario(req.model_dump())
        if res.get("ok"):
            plant = state.data.get("plant", "PLANT")
            payload = req.model_dump()
            historian.write_event(plant, res["applied"]["line"], res["applied"]["station"], payload.get("event","Scenario"), payload)
        return res
# ==================== OPC UA Explorer Endpoints ====================
    
    class OPCConnectReq(BaseModel):
        endpoint_url: str
        timeout: int = 5
    
    class OPCBrowseReq(BaseModel):
        node_id: str = "i=85"  # Objects folder by default
        max_depth: int = 1
    
    class OPCReadReq(BaseModel):
        node_id: str
    
    class OPCWriteReq(BaseModel):
        node_id: str
        value: Any
        data_type: Optional[str] = None
    
    class OPCSubscribeReq(BaseModel):
        node_id: str
        publishing_interval: int = 500
    
    class OPCUnsubscribeReq(BaseModel):
        node_id: str
    
    @app.post("/opcua/connect")
    async def opcua_connect(req: OPCConnectReq):
        """Connect to an OPC UA server"""
        try:
            result = await opcua_client.connect(req.endpoint_url, req.timeout)
            return {"ok": True, "connection": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/opcua/disconnect")
    async def opcua_disconnect():
        """Disconnect from current OPC UA server"""
        try:
            await opcua_client.disconnect()
            return {"ok": True, "connected": False}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/opcua/status")
    async def opcua_status():
        """Get connection status"""
        return {
            "ok": True,
            "connected": opcua_client.connected,
            "endpoint": opcua_client.endpoint_url
        }
    
    @app.post("/opcua/browse")
    async def opcua_browse(req: OPCBrowseReq):
        """Browse OPC UA address space"""
        try:
            result = await opcua_client.browse(req.node_id, req.max_depth)
            return {"ok": True, "browse": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/opcua/read")
    async def opcua_read(req: OPCReadReq):
        """Read a node value and attributes"""
        try:
            result = await opcua_client.read_node(req.node_id)
            return {"ok": True, "node": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/opcua/write")
    async def opcua_write(req: OPCWriteReq):
        """Write a value to a node"""
        try:
            result = await opcua_client.write_node(req.node_id, req.value, req.data_type)
            return {"ok": True, "write": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/opcua/subscribe")
    async def opcua_subscribe(req: OPCSubscribeReq):
        """Subscribe to node changes (add to watchlist)"""
        try:
            result = await opcua_client.subscribe_node(req.node_id, req.publishing_interval)
            return {"ok": True, "subscription": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/opcua/unsubscribe")
    async def opcua_unsubscribe(req: OPCUnsubscribeReq):
        """Unsubscribe from node (remove from watchlist)"""
        try:
            result = await opcua_client.unsubscribe_node(req.node_id)
            return {"ok": True, "unsubscription": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/opcua/watchlist")
    async def opcua_watchlist():
        """Get current watchlist with latest values"""
        try:
            result = await opcua_client.get_watchlist()
            return {"ok": True, "watchlist": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== Semantic Mapping Endpoints ====================
    
    class SemanticTransformReq(BaseModel):
        raw_data: Dict[str, Any]
        station_type: str
        station_metadata: Optional[Dict[str, Any]] = None
    
    @app.get("/semantic/mappings")
    def get_semantic_mappings():
        """Get full YAML semantic mapping configuration"""
        return {
            "ok": True,
            "mappings": semantic_engine.get_mappings()
        }
    
    @app.get("/semantic/loss_categories")
    def get_loss_categories():
        """Get loss category taxonomy"""
        return {
            "ok": True,
            "loss_categories": semantic_engine.get_loss_categories()
        }
    
    @app.get("/semantic/kpis")
    def get_derived_kpis():
        """Get derived KPI definitions"""
        return {
            "ok": True,
            "kpis": semantic_engine.get_derived_kpis()
        }
    
    @app.get("/semantic/station_types")
    def get_station_types():
        """Get available station type semantic models"""
        station_types = list(semantic_engine.station_types.keys())
        return {
            "ok": True,
            "station_types": station_types,
            "count": len(station_types)
        }
    
    @app.post("/semantic/transform")
    def transform_to_semantic(req: SemanticTransformReq):
        """Transform raw OPC UA data to semantic signals"""
        try:
            # Apply semantic mapping
            semantic_signals = semantic_engine.apply_semantic_mapping(
                raw_data=req.raw_data,
                station_type=req.station_type,
                station_metadata=req.station_metadata
            )
            
            # Validate signals
            validation = semantic_engine.validate_semantic_signals(semantic_signals)
            
            # Calculate KPIs
            kpis = semantic_engine.calculate_kpis(semantic_signals)
            
            return {
                "ok": True,
                "semantic_signals": semantic_signals,
                "kpis": kpis,
                "validation": validation,
                "count": len(semantic_signals)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/semantic/signals")
    def get_semantic_signals():
        """Get real-time semantic signals from current plant state"""
        try:
            # Get current snapshot
            snapshot = state.snapshot()
            plant_data_dict = snapshot.get('data', {}).get('lines', {})
            
            all_semantic_signals = []
            all_kpis = []
            
            # Transform each line's stations (snapshot uses dict format)
            for line_id, line_data in plant_data_dict.items():
                stations_dict = line_data.get('stations', {})
                
                # Iterate over stations dict
                for station_id, station_data in stations_dict.items():
                    station_name = station_data.get('name', station_id)
                    station_type = station_data.get('type', 'generic')
                    
                    # Extract raw data from station
                    raw_data = {
                        'Status': station_data.get('state', 'IDLE'),
                        'Temperature': station_data.get('temperature', 0),
                        'Speed': station_data.get('speed', 0),
                        'ProductCount': station_data.get('good_count', 0),
                        'CycleTime': station_data.get('cycle_time_s', 0)
                    }
                    
                    # Metadata for traceability
                    metadata = {
                        'station_id': station_id,
                        'station_name': station_name,
                        'line_id': line_id,
                        'plant': snapshot.get('data', {}).get('plant', 'PLANT')
                    }
                    
                    # Apply semantic mapping
                    signals = semantic_engine.apply_semantic_mapping(
                        raw_data=raw_data,
                        station_type=station_type,
                        station_metadata=metadata
                    )
                    
                    all_semantic_signals.extend(signals)
                    
                    # Calculate KPIs for this station
                    station_kpis = semantic_engine.calculate_kpis(signals)
                    all_kpis.extend(station_kpis)
            
            return {
                "ok": True,
                "timestamp": snapshot.get('data', {}).get('timestamp'),
                "semantic_signals": all_semantic_signals,
                "kpis": all_kpis,
                "signal_count": len(all_semantic_signals),
                "kpi_count": len(all_kpis)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/semantic/signals/{line_id}/{station_id}")
    def get_station_semantic_signals(line_id: str, station_id: str):
        """Get semantic signals for a specific station"""
        try:
            snapshot = state.snapshot()
            lines_dict = snapshot.get('data', {}).get('lines', {})
            
            # Find the station in dict structure
            if line_id not in lines_dict:
                raise HTTPException(
                    status_code=404,
                    detail=f"Line {line_id} not found"
                )
            
            line_data = lines_dict[line_id]
            stations_dict = line_data.get('stations', {})
            
            if station_id not in stations_dict:
                raise HTTPException(
                    status_code=404,
                    detail=f"Station {station_id} not found in line {line_id}"
                )
            
            target_station = stations_dict[station_id]
            
            # Extract raw data
            raw_data = {
                'Status': target_station.get('state', 'IDLE'),
                'Temperature': target_station.get('temperature', 0),
                'Speed': target_station.get('speed', 0),
                'ProductCount': target_station.get('good_count', 0),
                'CycleTime': target_station.get('cycle_time_s', 0)
            }
            
            metadata = {
                'station_id': station_id,
                'station_name': target_station.get('name', station_id),
                'line_id': line_id,
                'plant': snapshot.get('data', {}).get('plant', 'PLANT')
            }
            
            # Apply semantic mapping
            station_type = target_station.get('type', 'generic')
            signals = semantic_engine.apply_semantic_mapping(
                raw_data=raw_data,
                station_type=station_type,
                station_metadata=metadata
            )
            
            # Calculate KPIs
            kpis = semantic_engine.calculate_kpis(signals)
            
            # Validation
            validation = semantic_engine.validate_semantic_signals(signals)
            
            return {
                "ok": True,
                "station_id": station_id,
                "line_id": line_id,
                "station_type": station_type,
                "semantic_signals": signals,
                "kpis": kpis,
                "validation": validation
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    
    return app
