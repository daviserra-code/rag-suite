"""
OPC UA External Server Stub Provider - Sprint 7

Stub implementation for external OPC UA server integration.
Returns deterministic mock data for real-time equipment data.

DO NOT implement real OPC UA connection in this sprint.

Note: This is for EXTERNAL OPC UA servers (not the demo OPC server).
"""

from typing import Optional, Dict, Any
from .interface import ExternalContextProvider


class OPCUAStubProvider(ExternalContextProvider):
    """
    Stub provider for external OPC UA server integration.
    
    Future implementation would connect to:
    - PLC OPC UA servers (Siemens, Allen-Bradley, etc.)
    - SCADA OPC UA servers
    - DCS (Distributed Control System) OPC UA servers
    - IoT gateway OPC UA servers
    
    Currently returns mock data only.
    """
    
    def get_material_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get material handling data from OPC UA (stub).
        
        Real implementation would query:
        - Material presence sensors
        - Part counter values
        - Barcode scanner data
        """
        if not self.enabled:
            return None
        
        return {
            "source": "OPCUA_MATERIAL_STUB",
            "material_present": hash(equipment_id) % 2 == 0,
            "parts_counted": hash(equipment_id) % 100,
            "barcode_last_read": f"BC-{hash(equipment_id) % 10000:06d}",
            "feeder_level_percent": 50 + (hash(equipment_id) % 50),
            "material_type_detected": f"TYPE-{hash(equipment_id) % 10:02d}"
        }
    
    def get_quality_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get quality sensor data from OPC UA (stub).
        
        Real implementation would query:
        - Vision system results
        - Dimensional measurement data
        - Test equipment results
        """
        if not self.enabled:
            return None
        
        return {
            "source": "OPCUA_QUALITY_STUB",
            "vision_inspection_result": "PASS" if hash(equipment_id) % 10 < 9 else "FAIL",
            "dimensional_measurements": {
                "x_axis_mm": 100.0 + (hash(equipment_id) % 10) * 0.01,
                "y_axis_mm": 50.0 + (hash(equipment_id) % 10) * 0.01,
                "tolerance_met": True
            },
            "leak_test_result": "PASS",
            "functional_test_result": "PASS",
            "quality_gate_status": "RELEASED"
        }
    
    def get_tooling_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tool monitoring data from OPC UA (stub).
        
        Real implementation would query:
        - Tool wear sensors
        - Tool change counters
        - Spindle monitoring data
        """
        if not self.enabled:
            return None
        
        return {
            "source": "OPCUA_TOOLING_STUB",
            "tool_id": f"TOOL-{hash(equipment_id) % 100:03d}",
            "tool_life_percent": 100 - (hash(equipment_id) % 80),
            "tool_changes_count": hash(equipment_id) % 50,
            "spindle_hours": hash(equipment_id) % 1000,
            "vibration_level": 0.5 + (hash(equipment_id) % 10) * 0.1,
            "temperature_celsius": 25 + (hash(equipment_id) % 20)
        }
    
    def get_process_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time process data from OPC UA (stub).
        
        Real implementation would query:
        - PLC process variables
        - Recipe parameters
        - Control loop setpoints
        """
        if not self.enabled:
            return None
        
        return {
            "source": "OPCUA_PROCESS_STUB",
            "machine_state": ["IDLE", "RUNNING", "PAUSED", "ALARM"][hash(equipment_id) % 4],
            "cycle_time_current": 30 + (hash(equipment_id) % 10),
            "cycle_time_target": 35,
            "speed_rpm": 1000 + (hash(equipment_id) % 500),
            "temperature_actual": 25.0 + (hash(equipment_id) % 15),
            "temperature_setpoint": 30.0,
            "pressure_bar": 5.0 + (hash(equipment_id) % 10) * 0.1,
            "power_consumption_kw": 10 + (hash(equipment_id) % 20),
            "alarm_active": hash(equipment_id) % 20 == 0,
            "warning_active": hash(equipment_id) % 10 == 0
        }
    
    def get_traceability_context(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get traceability data from OPC UA (stub).
        
        Real implementation would query:
        - Serial number tracking
        - RFID reader data
        - Assembly verification data
        """
        if not self.enabled:
            return None
        
        return {
            "source": "OPCUA_TRACEABILITY_STUB",
            "serial_number_scanned": f"SN-{equipment_id}-{hash(equipment_id) % 10000:06d}",
            "rfid_tag_id": f"RFID-{hash(equipment_id) % 10000:08d}",
            "assembly_verification": {
                "torque_verified": True,
                "torque_value_nm": 25 + (hash(equipment_id) % 10),
                "angle_verified": True,
                "angle_value_deg": 90 + (hash(equipment_id) % 20)
            },
            "timestamp": "2025-12-25T10:30:00Z"
        }
