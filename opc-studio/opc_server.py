"""
OPC UA Server Manager
Creates and manages the OPC UA server with plant semantic model
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from asyncua import Server, ua
from asyncua.common.methods import uamethod

logger = logging.getLogger(__name__)


class OPCUAServerManager:
    """Manages OPC UA server for plant simulation"""
    
    def __init__(self, plant_model):
        self.plant_model = plant_model
        self.server: Optional[Server] = None
        self.namespace_idx: Optional[int] = None
        self.node_registry: Dict[str, ua.NodeId] = {}
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the OPC UA server"""
        opc_port = int(os.getenv("OPC_UA_PORT", "4840"))
        
        self.server = Server()
        await self.server.init()
        
        # Set server parameters
        self.server.set_endpoint(f"opc.tcp://0.0.0.0:{opc_port}/opcua")
        self.server.set_server_name("Shopfloor-Copilot OPC UA Server")
        
        # Set security policy (None for MVP)
        security_mode = os.getenv("OPC_SECURITY_MODE", "None")
        if security_mode == "None":
            self.server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
        
        # Register namespace
        self.namespace_idx = await self.server.register_namespace("http://shopfloor-copilot.local")
        logger.info(f"Registered namespace with index {self.namespace_idx}")
        
        # Build plant model structure in OPC UA
        await self._build_plant_structure()
        
        # Start server (don't use async with - we manage lifecycle manually)
        await self.server.start()
        logger.info(f"OPC UA server started on opc.tcp://0.0.0.0:{opc_port}/opcua")
        self._running = True
        
        # Start periodic update task
        self._update_task = asyncio.create_task(self._update_values_loop())
        logger.info("Started OPC value update loop")
    
    async def stop(self):
        """Stop the OPC UA server"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        if self.server:
            await self.server.stop()
        logger.info("OPC UA server stopped")
    
    def is_running(self) -> bool:
        """Check if server is running"""
        return self._running
    
    def get_nodes_count(self) -> int:
        """Get number of nodes in registry"""
        return len(self.node_registry)
    
    async def _build_plant_structure(self):
        """Build OPC UA node structure from plant model"""
        objects = self.server.nodes.objects
        
        # Create Plant root object
        plant_node = await objects.add_object(self.namespace_idx, "Plant")
        self.node_registry["Plant"] = plant_node.nodeid
        
        # Add production lines
        for line in self.plant_model.production_lines:
            line_path = f"Plant.{line.line_id}"
            line_node = await plant_node.add_object(self.namespace_idx, line.line_id)
            self.node_registry[line_path] = line_node.nodeid
            
            # Add line properties
            await line_node.add_variable(self.namespace_idx, "LineName", line.line_name)
            oee_var = await line_node.add_variable(self.namespace_idx, "OEE", 0.0)
            await oee_var.set_writable()
            self.node_registry[f"{line_path}.OEE"] = oee_var.nodeid
            
            availability_var = await line_node.add_variable(self.namespace_idx, "Availability", 0.0)
            await availability_var.set_writable()
            self.node_registry[f"{line_path}.Availability"] = availability_var.nodeid
            
            performance_var = await line_node.add_variable(self.namespace_idx, "Performance", 0.0)
            await performance_var.set_writable()
            self.node_registry[f"{line_path}.Performance"] = performance_var.nodeid
            
            quality_var = await line_node.add_variable(self.namespace_idx, "Quality", 0.0)
            await quality_var.set_writable()
            self.node_registry[f"{line_path}.Quality"] = quality_var.nodeid
            
            # Add stations
            for station in line.stations:
                station_path = f"{line_path}.{station.station_id}"
                station_node = await line_node.add_object(self.namespace_idx, station.station_id)
                self.node_registry[station_path] = station_node.nodeid
                
                # Add station properties
                await station_node.add_variable(self.namespace_idx, "StationName", station.station_name)
                
                status_var = await station_node.add_variable(self.namespace_idx, "Status", "Running")
                await status_var.set_writable()
                self.node_registry[f"{station_path}.Status"] = status_var.nodeid
                
                temp_var = await station_node.add_variable(self.namespace_idx, "Temperature", 25.0)
                await temp_var.set_writable()
                self.node_registry[f"{station_path}.Temperature"] = temp_var.nodeid
                
                cycle_time_var = await station_node.add_variable(self.namespace_idx, "CycleTime", 60.0)
                await cycle_time_var.set_writable()
                self.node_registry[f"{station_path}.CycleTime"] = cycle_time_var.nodeid
        
        logger.info(f"Built OPC UA structure with {len(self.node_registry)} nodes")
    
    async def _update_values_loop(self):
        """Periodically update OPC UA node values with simulated data"""
        try:
            while self._running:
                await self._update_simulated_values()
                await asyncio.sleep(5)  # Update every 5 seconds
        except asyncio.CancelledError:
            logger.info("Update loop cancelled")
    
    async def _update_simulated_values(self):
        """Update OPC UA nodes with simulated values"""
        import random
        
        for line in self.plant_model.production_lines:
            line_path = f"Plant.{line.line_id}"
            
            # Simulate OEE metrics with realistic values
            availability = random.uniform(0.85, 0.98)
            performance = random.uniform(0.80, 0.95)
            quality = random.uniform(0.92, 0.99)
            oee = availability * performance * quality
            
            try:
                # Get node objects and write values
                oee_node = self.server.get_node(self.node_registry[f"{line_path}.OEE"])
                await oee_node.write_value(oee)
                
                avail_node = self.server.get_node(self.node_registry[f"{line_path}.Availability"])
                await avail_node.write_value(availability)
                
                perf_node = self.server.get_node(self.node_registry[f"{line_path}.Performance"])
                await perf_node.write_value(performance)
                
                qual_node = self.server.get_node(self.node_registry[f"{line_path}.Quality"])
                await qual_node.write_value(quality)
            except Exception as e:
                logger.error(f"Error updating line {line.line_id}: {e}")
            
            # Update stations
            for station in line.stations:
                station_path = f"{line_path}.{station.station_id}"
                
                try:
                    # Simulate temperature
                    temp_node = self.server.get_node(self.node_registry[f"{station_path}.Temperature"])
                    await temp_node.write_value(random.uniform(20.0, 35.0))
                    
                    # Simulate cycle time
                    cycle_node = self.server.get_node(self.node_registry[f"{station_path}.CycleTime"])
                    await cycle_node.write_value(random.uniform(50.0, 70.0))
                except Exception as e:
                    logger.error(f"Error updating station {station.station_id}: {e}")
    
    async def browse_nodes(self, node_id: Optional[str] = None) -> List[dict]:
        """Browse OPC UA namespace"""
        if not self.server:
            return []
        
        try:
            if node_id:
                node = self.server.get_node(node_id)
            else:
                node = self.server.nodes.objects
            
            children = await node.get_children()
            result = []
            
            for child in children:
                browse_name = await child.read_browse_name()
                node_class = await child.read_node_class()
                
                result.append({
                    "node_id": child.nodeid.to_string(),
                    "browse_name": browse_name.Name,
                    "node_class": node_class.name
                })
            
            return result
        except Exception as e:
            logger.error(f"Error browsing nodes: {e}")
            return []
    
    async def read_node(self, node_path: str):
        """Read value from OPC UA node by path"""
        if node_path not in self.node_registry:
            raise ValueError(f"Node path {node_path} not found")
        
        node = self.server.get_node(self.node_registry[node_path])
        value = await node.read_value()
        return value
    
    async def write_node(self, node_path: str, value):
        """Write value to OPC UA node by path"""
        if node_path not in self.node_registry:
            raise ValueError(f"Node path {node_path} not found")
        
        node = self.server.get_node(self.node_registry[node_path])
        await node.write_value(value)
