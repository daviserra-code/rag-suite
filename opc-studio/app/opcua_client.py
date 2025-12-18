"""
OPC UA Client for OPC Explorer
Provides connect, browse, read, and subscribe functionality
"""
import asyncio
from typing import Dict, List, Optional, Any
from asyncua import Client, ua
import logging

logger = logging.getLogger(__name__)


class WatchlistHandler:
    """Subscription handler for watchlist monitoring"""
    
    def __init__(self):
        self.data_changes: Dict[str, Any] = {}
        self.last_values: Dict[str, Any] = {}
    
    def datachange_notification(self, node, val, data):
        """Called when a monitored node value changes"""
        node_id = str(node)
        self.data_changes[node_id] = {
            "value": val,
            "timestamp": data.monitored_item.Value.ServerTimestamp.isoformat() if data.monitored_item.Value.ServerTimestamp else None,
            "status": str(data.monitored_item.Value.StatusCode)
        }
        self.last_values[node_id] = val
        logger.info(f"Data change: {node_id} = {val}")


class OPCUAClient:
    """OPC UA Client wrapper for explorer functionality"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.connected: bool = False
        self.endpoint_url: Optional[str] = None
        self.subscription = None
        self.handler = WatchlistHandler()
        self.monitored_nodes: Dict[str, Any] = {}  # node_id -> handle
        
    async def connect(self, endpoint_url: str, timeout: int = 5) -> Dict[str, Any]:
        """Connect to OPC UA server"""
        try:
            if self.connected:
                await self.disconnect()
            
            self.client = Client(url=endpoint_url, timeout=timeout)
            await self.client.connect()
            
            self.endpoint_url = endpoint_url
            self.connected = True
            
            # Get server info
            try:
                namespaces = await self.client.get_namespace_array()
            except:
                namespaces = []
            
            logger.info(f"Connected to {endpoint_url}")
            
            return {
                "connected": True,
                "endpoint": endpoint_url,
                "namespaces": namespaces
            }
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connected = False
            raise Exception(f"Failed to connect to {endpoint_url}: {str(e)}")
    
    async def disconnect(self):
        """Disconnect from OPC UA server"""
        if self.client and self.connected:
            try:
                # Delete subscription if exists
                if self.subscription:
                    await self.subscription.delete()
                    self.subscription = None
                    self.monitored_nodes.clear()
                
                await self.client.disconnect()
                logger.info(f"Disconnected from {self.endpoint_url}")
            except Exception as e:
                logger.error(f"Disconnect error: {e}")
            finally:
                self.connected = False
                self.client = None
    
    async def browse(self, node_id: str = "i=85", max_depth: int = 1) -> Dict[str, Any]:
        """
        Browse OPC UA address space from a given node
        node_id: NodeId string (e.g., "i=85" for Objects folder)
        max_depth: How many levels to browse (1 = direct children only)
        """
        if not self.connected or not self.client:
            raise Exception("Not connected to OPC UA server")
        
        try:
            node = self.client.get_node(node_id)
            
            # Get node attributes
            browse_name = await node.read_browse_name()
            display_name = await node.read_display_name()
            node_class = await node.read_node_class()
            
            result = {
                "node_id": node_id,
                "browse_name": f"{browse_name.NamespaceIndex}:{browse_name.Name}",
                "display_name": display_name.Text,
                "node_class": str(node_class),
                "children": []
            }
            
            # Browse children
            if max_depth > 0:
                children = await node.get_children()
                for child in children:
                    child_id = child.nodeid.to_string()
                    child_browse_name = await child.read_browse_name()
                    child_display_name = await child.read_display_name()
                    child_node_class = await child.read_node_class()
                    
                    child_data = {
                        "node_id": child_id,
                        "browse_name": f"{child_browse_name.NamespaceIndex}:{child_browse_name.Name}",
                        "display_name": child_display_name.Text,
                        "node_class": str(child_node_class),
                        "has_children": len(await child.get_children()) > 0 if max_depth > 1 else False
                    }
                    
                    # Recursively browse if max_depth > 1
                    if max_depth > 1:
                        nested = await self.browse(child_id, max_depth - 1)
                        child_data["children"] = nested.get("children", [])
                    
                    result["children"].append(child_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Browse error for {node_id}: {e}")
            raise Exception(f"Failed to browse node {node_id}: {str(e)}")
    
    async def read_node(self, node_id: str) -> Dict[str, Any]:
        """Read value and attributes from a node"""
        if not self.connected or not self.client:
            raise Exception("Not connected to OPC UA server")
        
        try:
            node = self.client.get_node(node_id)
            
            # Read attributes
            browse_name = await node.read_browse_name()
            display_name = await node.read_display_name()
            node_class = await node.read_node_class()
            
            result = {
                "node_id": node_id,
                "browse_name": f"{browse_name.NamespaceIndex}:{browse_name.Name}",
                "display_name": display_name.Text,
                "node_class": str(node_class),
                "value": None,
                "data_type": None,
                "timestamp": None,
                "status": None
            }
            
            # Try to read value if it's a Variable
            if node_class == ua.NodeClass.Variable:
                try:
                    data_value = await node.read_data_value()
                    result["value"] = data_value.Value.Value
                    result["data_type"] = str(data_value.Value.VariantType)
                    result["timestamp"] = data_value.ServerTimestamp.isoformat() if data_value.ServerTimestamp else None
                    result["status"] = str(data_value.StatusCode)
                except Exception as e:
                    logger.warning(f"Could not read value from {node_id}: {e}")
                    result["value"] = f"<error: {str(e)}>"
            
            return result
            
        except Exception as e:
            logger.error(f"Read error for {node_id}: {e}")
            raise Exception(f"Failed to read node {node_id}: {str(e)}")
    
    async def write_node(self, node_id: str, value: Any, data_type: Optional[str] = None) -> Dict[str, Any]:
        """Write value to a node"""
        if not self.connected or not self.client:
            raise Exception("Not connected to OPC UA server")
        
        try:
            node = self.client.get_node(node_id)
            
            # Convert value to appropriate type if data_type specified
            if data_type:
                variant_type = getattr(ua.VariantType, data_type, None)
                if variant_type:
                    value = ua.Variant(value, variant_type)
            
            await node.write_value(value)
            
            # Read back to confirm
            new_value = await node.read_value()
            
            return {
                "success": True,
                "node_id": node_id,
                "written_value": value,
                "current_value": new_value
            }
            
        except Exception as e:
            logger.error(f"Write error for {node_id}: {e}")
            raise Exception(f"Failed to write to node {node_id}: {str(e)}")
    
    async def subscribe_node(self, node_id: str, publishing_interval: int = 500) -> Dict[str, Any]:
        """Add a node to the watchlist (subscription)"""
        if not self.connected or not self.client:
            raise Exception("Not connected to OPC UA server")
        
        try:
            # Create subscription if it doesn't exist
            if not self.subscription:
                self.subscription = await self.client.create_subscription(publishing_interval, self.handler)
                logger.info(f"Created subscription with {publishing_interval}ms interval")
            
            # Check if already monitoring
            if node_id in self.monitored_nodes:
                return {
                    "success": True,
                    "node_id": node_id,
                    "message": "Already monitoring this node"
                }
            
            # Subscribe to node
            node = self.client.get_node(node_id)
            handle = await self.subscription.subscribe_data_change(node)
            self.monitored_nodes[node_id] = handle
            
            logger.info(f"Subscribed to {node_id}")
            
            return {
                "success": True,
                "node_id": node_id,
                "monitoring": True,
                "publishing_interval_ms": publishing_interval
            }
            
        except Exception as e:
            logger.error(f"Subscribe error for {node_id}: {e}")
            raise Exception(f"Failed to subscribe to node {node_id}: {str(e)}")
    
    async def unsubscribe_node(self, node_id: str) -> Dict[str, Any]:
        """Remove a node from the watchlist"""
        if not self.connected or not self.client:
            raise Exception("Not connected to OPC UA server")
        
        try:
            if node_id not in self.monitored_nodes:
                return {
                    "success": False,
                    "node_id": node_id,
                    "message": "Node not in watchlist"
                }
            
            handle = self.monitored_nodes[node_id]
            await self.subscription.unsubscribe(handle)
            del self.monitored_nodes[node_id]
            
            logger.info(f"Unsubscribed from {node_id}")
            
            return {
                "success": True,
                "node_id": node_id,
                "monitoring": False
            }
            
        except Exception as e:
            logger.error(f"Unsubscribe error for {node_id}: {e}")
            raise Exception(f"Failed to unsubscribe from node {node_id}: {str(e)}")
    
    async def get_watchlist(self) -> Dict[str, Any]:
        """Get current watchlist with latest values"""
        if not self.connected:
            return {"connected": False, "watchlist": []}
        
        watchlist = []
        for node_id in self.monitored_nodes.keys():
            try:
                # Get node info
                node = self.client.get_node(node_id)
                display_name = await node.read_display_name()
                
                # Get latest value from handler
                latest = self.handler.last_values.get(node_id)
                change_info = self.handler.data_changes.get(node_id, {})
                
                watchlist.append({
                    "node_id": node_id,
                    "display_name": display_name.Text,
                    "value": latest,
                    "timestamp": change_info.get("timestamp"),
                    "status": change_info.get("status")
                })
            except Exception as e:
                logger.warning(f"Error getting watchlist info for {node_id}: {e}")
        
        return {
            "connected": True,
            "watchlist": watchlist,
            "monitoring_count": len(self.monitored_nodes)
        }


# Global client instance
_client = OPCUAClient()


def get_client() -> OPCUAClient:
    """Get the global OPC UA client instance"""
    return _client
