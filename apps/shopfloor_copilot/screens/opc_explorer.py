"""
OPC Explorer Screen - UAExpert-like functionality
Connect, browse, read, and subscribe to OPC UA servers
"""
from nicegui import ui
import httpx
import asyncio
import os
from typing import Optional, Dict, Any


OPC_API = "http://opc-studio:8040"


class OPCExplorerScreen:
    """OPC UA Explorer interface"""
    
    def __init__(self):
        self.connected = False
        # Get endpoint from environment variable with fallback
        # Production: opc.tcp://46.224.66.48:4850
        # Local: opc.tcp://opc-demo:4850
        self.endpoint_url = os.getenv("OPC_DEMO_ENDPOINT", "opc.tcp://opc-studio:4840/shopfloor/opc-studio")
        self.current_node = "i=85"  # Objects folder
        self.watchlist_items = []
        
        # UI components
        self.status_label: Optional[ui.label] = None
        self.tree_container: Optional[ui.column] = None
        self.node_details_container: Optional[ui.column] = None
        self.watchlist_container: Optional[ui.column] = None
        self.watchlist_timer: Optional[ui.timer] = None
    
    async def check_status(self):
        """Check OPC UA connection status"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{OPC_API}/opcua/status")
                data = resp.json()
                self.connected = data.get("connected", False)
                if self.status_label:
                    if self.connected:
                        self.status_label.text = f"🟢 Connected: {data.get('endpoint', 'Unknown')}"
                        self.status_label.style("color: green")
                    else:
                        self.status_label.text = "🔴 Not Connected"
                        self.status_label.style("color: red")
        except Exception as e:
            if self.status_label:
                self.status_label.text = f"⚠️ Error: {str(e)}"
                self.status_label.style("color: orange")
    
    async def connect(self):
        """Connect to OPC UA server"""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{OPC_API}/opcua/connect",
                    json={"endpoint_url": self.endpoint_url, "timeout": 10}
                )
                data = resp.json()
                
                if data.get("ok"):
                    ui.notify("✅ Connected successfully to OPC UA server!", type="positive", position="top", timeout=3000)
                    self.connected = True
                    await self.check_status()
                    await self.browse_node(self.current_node)
                else:
                    error_msg = data.get("error", "Unknown error")
                    ui.notify(f"❌ Connection failed: {error_msg}", type="negative", position="top", timeout=5000)
                    ui.notify("💡 Tip: Check if opc-studio and opc-demo services are running", type="info", position="top", timeout=5000)
        except httpx.TimeoutException:
            ui.notify("⏱️ Connection timeout - OPC Studio service may be unavailable", type="warning", position="top", timeout=5000)
        except Exception as e:
            ui.notify(f"⚠️ Connection error: {str(e)}", type="negative", position="top", timeout=5000)
            ui.notify("Check Docker services: docker compose ps", type="info", position="top", timeout=3000)
    
    async def disconnect(self):
        """Disconnect from OPC UA server"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(f"{OPC_API}/opcua/disconnect")
                data = resp.json()
                
                if data.get("ok"):
                    ui.notify("Disconnected", type="info")
                    self.connected = False
                    await self.check_status()
                    if self.tree_container:
                        self.tree_container.clear()
        except Exception as e:
            ui.notify(f"Disconnect error: {str(e)}", type="negative")
    
    async def browse_node(self, node_id: str, max_depth: int = 1):
        """Browse OPC UA node"""
        if not self.connected:
            ui.notify("Not connected to server", type="warning")
            return
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{OPC_API}/opcua/browse",
                    json={"node_id": node_id, "max_depth": max_depth}
                )
                data = resp.json()
                
                if data.get("ok"):
                    browse_data = data.get("browse", {})
                    self.current_node = node_id
                    await self.render_browse_tree(browse_data)
                else:
                    ui.notify("Browse failed", type="negative")
        except Exception as e:
            ui.notify(f"Browse error: {str(e)}", type="negative")
    
    async def render_browse_tree(self, browse_data: Dict[str, Any]):
        """Render browsed nodes in tree view"""
        if not self.tree_container:
            return
        
        self.tree_container.clear()
        
        with self.tree_container:
            # Current node header
            ui.label(f"📁 {browse_data.get('display_name', 'Unknown')}").classes("text-lg font-bold")
            ui.label(f"Node ID: {browse_data.get('node_id')}").classes("text-xs text-gray-500")
            ui.separator()
            
            # Children
            children = browse_data.get("children", [])
            if not children:
                ui.label("No children found").classes("text-gray-400 italic")
            else:
                for child in children:
                    await self.render_node_card(child)
    
    async def render_node_card(self, node: Dict[str, Any]):
        """Render a single node card"""
        node_id = node.get("node_id")
        display_name = node.get("display_name", "Unknown")
        node_class = node.get("node_class", "Unknown")
        has_children = node.get("has_children", False)
        
        # Icon based on node class
        icon = "📄" if "Variable" in node_class else "📁" if has_children else "📋"
        
        with ui.card().classes("w-full mb-2"):
            with ui.row().classes("w-full items-center"):
                ui.label(f"{icon} {display_name}").classes("text-sm font-semibold flex-grow")
                
                # Action buttons
                ui.button("Browse", on_click=lambda nid=node_id: self.browse_node(nid)).props("size=sm dense")
                ui.button("Read", on_click=lambda nid=node_id: self.read_node(nid)).props("size=sm dense color=primary")
                
                if "Variable" in node_class:
                    ui.button("Watch", on_click=lambda nid=node_id: self.add_to_watchlist(nid)).props("size=sm dense color=green")
            
            ui.label(f"Class: {node_class}").classes("text-xs text-gray-500")
            ui.label(f"ID: {node_id}").classes("text-xs text-gray-400 font-mono")
    
    async def read_node(self, node_id: str):
        """Read node value and display details"""
        if not self.connected:
            ui.notify("Not connected", type="warning")
            return
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(
                    f"{OPC_API}/opcua/read",
                    json={"node_id": node_id}
                )
                data = resp.json()
                
                if data.get("ok"):
                    node_data = data.get("node", {})
                    await self.show_node_details(node_data)
                else:
                    ui.notify("Read failed", type="negative")
        except Exception as e:
            ui.notify(f"Read error: {str(e)}", type="negative")
    
    async def show_node_details(self, node_data: Dict[str, Any]):
        """Show detailed node information"""
        if not self.node_details_container:
            return
        
        self.node_details_container.clear()
        
        with self.node_details_container:
            ui.label("Node Details").classes("text-lg font-bold mb-2")
            
            with ui.card().classes("w-full"):
                ui.label(f"Display Name: {node_data.get('display_name')}").classes("font-semibold")
                ui.label(f"Browse Name: {node_data.get('browse_name')}").classes("text-sm")
                ui.label(f"Node Class: {node_data.get('node_class')}").classes("text-sm")
                ui.label(f"Node ID: {node_data.get('node_id')}").classes("text-xs font-mono")
                ui.separator()
                
                value = node_data.get("value")
                if value is not None:
                    ui.label(f"Value: {value}").classes("text-lg text-blue-600 font-bold")
                    ui.label(f"Data Type: {node_data.get('data_type', 'Unknown')}").classes("text-sm")
                    ui.label(f"Timestamp: {node_data.get('timestamp', 'N/A')}").classes("text-xs")
                    ui.label(f"Status: {node_data.get('status', 'Unknown')}").classes("text-xs")
                else:
                    ui.label("No value (not a variable)").classes("text-gray-400 italic")
    
    async def add_to_watchlist(self, node_id: str):
        """Add node to watchlist"""
        if not self.connected:
            ui.notify("Not connected", type="warning")
            return
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(
                    f"{OPC_API}/opcua/subscribe",
                    json={"node_id": node_id, "publishing_interval": 1000}
                )
                data = resp.json()
                
                if data.get("ok"):
                    ui.notify("Added to watchlist", type="positive")
                    await self.refresh_watchlist()
                else:
                    ui.notify("Subscribe failed", type="negative")
        except Exception as e:
            ui.notify(f"Subscribe error: {str(e)}", type="negative")
    
    async def remove_from_watchlist(self, node_id: str):
        """Remove node from watchlist"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(
                    f"{OPC_API}/opcua/unsubscribe",
                    json={"node_id": node_id}
                )
                data = resp.json()
                
                if data.get("ok"):
                    ui.notify("Removed from watchlist", type="info")
                    await self.refresh_watchlist()
        except Exception as e:
            ui.notify(f"Unsubscribe error: {str(e)}", type="negative")
    
    async def refresh_watchlist(self):
        """Refresh watchlist display"""
        if not self.connected or not self.watchlist_container:
            return
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{OPC_API}/opcua/watchlist")
                data = resp.json()
                
                if data.get("ok"):
                    watchlist_data = data.get("watchlist", {})
                    self.watchlist_items = watchlist_data.get("watchlist", [])
                    await self.render_watchlist()
        except Exception as e:
            pass  # Silent fail for refresh
    
    async def render_watchlist(self):
        """Render watchlist table"""
        if not self.watchlist_container:
            return
        
        self.watchlist_container.clear()
        
        with self.watchlist_container:
            ui.label(f"Watchlist ({len(self.watchlist_items)} items)").classes("text-lg font-bold mb-2")
            
            if not self.watchlist_items:
                ui.label("No monitored nodes").classes("text-gray-400 italic")
            else:
                for item in self.watchlist_items:
                    with ui.card().classes("w-full mb-2"):
                        with ui.row().classes("w-full items-center"):
                            with ui.column().classes("flex-grow"):
                                ui.label(item.get("display_name", "Unknown")).classes("font-semibold")
                                ui.label(f"Value: {item.get('value')}").classes("text-lg text-green-600 font-bold")
                                ui.label(f"Updated: {item.get('timestamp', 'N/A')}").classes("text-xs text-gray-500")
                            
                            ui.button(
                                "Remove",
                                on_click=lambda nid=item.get("node_id"): self.remove_from_watchlist(nid)
                            ).props("size=sm dense color=red")
    
    def render(self):
        """Render the OPC Explorer UI"""
        with ui.column().classes("w-full h-full p-4"):
            # Header
            ui.label("🔍 OPC UA Explorer").classes("text-2xl font-bold mb-4")
            
            # Connection panel
            with ui.card().classes("w-full mb-4"):
                ui.label("Connection").classes("text-lg font-semibold mb-2")
                
                with ui.row().classes("w-full items-center gap-2"):
                    ui.input(
                        label="Endpoint URL",
                        value=self.endpoint_url,
                        on_change=lambda e: setattr(self, 'endpoint_url', e.value)
                    ).classes("flex-grow").props("dense")
                    
                    ui.button("Connect", on_click=self.connect).props("color=primary")
                    ui.button("Disconnect", on_click=self.disconnect).props("color=negative")
                
                self.status_label = ui.label("🔴 Not Connected").classes("text-sm")
                self.status_label.style("color: red")
            
            # Main layout: Browser + Details + Watchlist
            with ui.row().classes("w-full gap-4"):
                # Left: Address Space Browser
                with ui.column().classes("w-1/2"):
                    with ui.card().classes("w-full"):
                        ui.label("📂 Address Space Browser").classes("text-lg font-semibold mb-2")
                        
                        with ui.row().classes("w-full mb-2"):
                            ui.button(
                                "Browse Root",
                                on_click=lambda: self.browse_node("i=85")
                            ).props("size=sm dense")
                            ui.button(
                                "Refresh",
                                on_click=lambda: self.browse_node(self.current_node)
                            ).props("size=sm dense")
                        
                        self.tree_container = ui.column().classes("w-full").style("max-height: 500px; overflow-y: auto")
                
                # Right: Node Details + Watchlist
                with ui.column().classes("w-1/2 gap-4"):
                    # Node Details
                    with ui.card().classes("w-full"):
                        self.node_details_container = ui.column().classes("w-full")
                        with self.node_details_container:
                            ui.label("Select a node to view details").classes("text-gray-400 italic")
                    
                    # Watchlist
                    with ui.card().classes("w-full"):
                        self.watchlist_container = ui.column().classes("w-full").style("max-height: 400px; overflow-y: auto")
                        with self.watchlist_container:
                            ui.label("Watchlist (0 items)").classes("text-lg font-bold")
                            ui.label("No monitored nodes").classes("text-gray-400 italic")
        
        # Start status check and watchlist refresh timers
        ui.timer(2.0, self.check_status)
        self.watchlist_timer = ui.timer(2.0, self.refresh_watchlist)
        
        # Initial status check
        asyncio.create_task(self.check_status())


def render_opc_explorer():
    """Render OPC Explorer screen"""
    screen = OPCExplorerScreen()
    screen.render()
