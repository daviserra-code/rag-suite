"""
Scenario Engine - Inject what-if scenarios into plant simulation
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Scenario:
    """Represents an active scenario"""
    
    def __init__(
        self,
        scenario_id: str,
        scenario_type: str,
        target_line: str,
        target_station: Optional[str],
        duration_minutes: int,
        severity: str,
        parameters: dict
    ):
        self.scenario_id = scenario_id
        self.scenario_type = scenario_type
        self.target_line = target_line
        self.target_station = target_station
        self.duration_minutes = duration_minutes
        self.severity = severity
        self.parameters = parameters
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=duration_minutes)
        self.active = True
    
    def is_expired(self) -> bool:
        """Check if scenario has expired"""
        return datetime.now() >= self.end_time
    
    def to_dict(self) -> dict:
        """Export to dict"""
        return {
            "scenario_id": self.scenario_id,
            "scenario_type": self.scenario_type,
            "target_line": self.target_line,
            "target_station": self.target_station,
            "duration_minutes": self.duration_minutes,
            "severity": self.severity,
            "parameters": self.parameters,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "active": self.active,
            "time_remaining_minutes": max(0, (self.end_time - datetime.now()).total_seconds() / 60)
        }


class ScenarioEngine:
    """Manages what-if scenarios for plant simulation"""
    
    def __init__(self, opc_server, plant_model):
        self.opc_server = opc_server
        self.plant_model = plant_model
        self.active_scenarios: Dict[str, Scenario] = {}
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Start monitoring
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_scenarios())
    
    async def inject_scenario(
        self,
        scenario_type: str,
        target_line: str,
        target_station: Optional[str] = None,
        duration_minutes: int = 30,
        severity: str = "medium",
        parameters: dict = None
    ) -> str:
        """Inject a new scenario"""
        scenario_id = str(uuid.uuid4())[:8]
        
        scenario = Scenario(
            scenario_id=scenario_id,
            scenario_type=scenario_type,
            target_line=target_line,
            target_station=target_station,
            duration_minutes=duration_minutes,
            severity=severity,
            parameters=parameters or {}
        )
        
        self.active_scenarios[scenario_id] = scenario
        
        # Apply scenario effects
        await self._apply_scenario(scenario)
        
        logger.info(f"Injected scenario {scenario_id}: {scenario_type} on {target_line}")
        
        return scenario_id
    
    async def stop_scenario(self, scenario_id: str):
        """Stop an active scenario"""
        if scenario_id not in self.active_scenarios:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        scenario = self.active_scenarios[scenario_id]
        scenario.active = False
        
        # Restore normal operation
        await self._restore_normal(scenario)
        
        del self.active_scenarios[scenario_id]
        
        logger.info(f"Stopped scenario {scenario_id}")
    
    def get_active_scenarios(self) -> List[dict]:
        """Get all active scenarios"""
        return [s.to_dict() for s in self.active_scenarios.values() if s.active]
    
    async def _monitor_scenarios(self):
        """Monitor and expire scenarios"""
        try:
            while self._running:
                expired = []
                
                for scenario_id, scenario in self.active_scenarios.items():
                    if scenario.is_expired():
                        expired.append(scenario_id)
                
                # Remove expired scenarios
                for scenario_id in expired:
                    await self.stop_scenario(scenario_id)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except asyncio.CancelledError:
            logger.info("Scenario monitor cancelled")
    
    async def _apply_scenario(self, scenario: Scenario):
        """Apply scenario effects to OPC UA nodes"""
        try:
            line_path = f"Plant.{scenario.target_line}"
            
            # Severity impact factors
            severity_factors = {
                "low": 0.95,
                "medium": 0.85,
                "high": 0.70
            }
            impact = severity_factors.get(scenario.severity, 0.85)
            
            # Apply different effects based on scenario type
            if scenario.scenario_type == "EquipmentFailure":
                # Reduce availability significantly
                availability_node = f"{line_path}.Availability"
                await self.opc_server.write_node(availability_node, impact * 0.6)
                
                # If specific station, mark it as down
                if scenario.target_station:
                    station_path = f"{line_path}.{scenario.target_station}"
                    status_node = f"{station_path}.Status"
                    await self.opc_server.write_node(status_node, "Down")
            
            elif scenario.scenario_type == "QualityIssue":
                # Reduce quality
                quality_node = f"{line_path}.Quality"
                await self.opc_server.write_node(quality_node, impact)
            
            elif scenario.scenario_type == "MaterialShortage":
                # Reduce performance
                performance_node = f"{line_path}.Performance"
                await self.opc_server.write_node(performance_node, impact * 0.8)
            
            elif scenario.scenario_type == "ProcessSlowdown":
                # Reduce performance
                performance_node = f"{line_path}.Performance"
                await self.opc_server.write_node(performance_node, impact)
            
            elif scenario.scenario_type == "MaintenanceRequired":
                # Moderate impact on all metrics
                await self.opc_server.write_node(f"{line_path}.Availability", impact * 0.9)
                await self.opc_server.write_node(f"{line_path}.Performance", impact * 0.95)
            
            logger.info(f"Applied scenario effects: {scenario.scenario_type} with severity {scenario.severity}")
            
        except Exception as e:
            logger.error(f"Error applying scenario: {e}")
    
    async def _restore_normal(self, scenario: Scenario):
        """Restore normal operation after scenario ends"""
        try:
            line_path = f"Plant.{scenario.target_line}"
            
            # Restore to typical values
            await self.opc_server.write_node(f"{line_path}.Availability", 0.92)
            await self.opc_server.write_node(f"{line_path}.Performance", 0.88)
            await self.opc_server.write_node(f"{line_path}.Quality", 0.96)
            
            # Restore station status if specific station was affected
            if scenario.target_station:
                station_path = f"{line_path}.{scenario.target_station}"
                status_node = f"{station_path}.Status"
                await self.opc_server.write_node(status_node, "Running")
            
            logger.info(f"Restored normal operation for {scenario.target_line}")
            
        except Exception as e:
            logger.error(f"Error restoring normal operation: {e}")
