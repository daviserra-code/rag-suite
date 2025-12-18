"""
Semantic Signals Screen
Displays raw OPC UA tags vs semantic MES signals with loss_category classification
"""
from nicegui import ui
import httpx
import asyncio
from typing import Optional, Dict, Any, List


OPC_API = "http://opc-studio:8040"


class SemanticSignalsScreen:
    """Semantic mapping visualization"""
    
    def __init__(self):
        self.semantic_signals: List[Dict[str, Any]] = []
        self.kpis: List[Dict[str, Any]] = []
        self.loss_categories: Dict[str, List[str]] = {}
        self.selected_line = "A01"
        self.selected_station = "ST17"
        
        # UI components
        self.signals_container: Optional[ui.column] = None
        self.kpis_container: Optional[ui.column] = None
        self.loss_category_container: Optional[ui.column] = None
        self.refresh_timer: Optional[ui.timer] = None
    
    async def load_loss_categories(self):
        """Load loss category taxonomy"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{OPC_API}/semantic/loss_categories")
                data = resp.json()
                
                if data.get("ok"):
                    self.loss_categories = data.get("loss_categories", {})
        except Exception as e:
            ui.notify(f"Failed to load loss categories: {str(e)}", type="negative")
    
    async def load_semantic_signals(self):
        """Load all semantic signals from plant"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{OPC_API}/semantic/signals")
                data = resp.json()
                
                if data.get("ok"):
                    self.semantic_signals = data.get("semantic_signals", [])
                    self.kpis = data.get("kpis", [])
                    await self.render_signals()
                    await self.render_kpis()
        except Exception as e:
            ui.notify(f"Failed to load semantic signals: {str(e)}", type="negative")
    
    async def load_station_signals(self):
        """Load semantic signals for selected station"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                url = f"{OPC_API}/semantic/signals/{self.selected_line}/{self.selected_station}"
                resp = await client.get(url)
                data = resp.json()
                
                if data.get("ok"):
                    signals = data.get("semantic_signals", [])
                    kpis = data.get("kpis", [])
                    validation = data.get("validation", {})
                    
                    await self.render_station_details(signals, kpis, validation)
        except Exception as e:
            ui.notify(f"Failed to load station signals: {str(e)}", type="negative")
    
    async def render_signals(self):
        """Render semantic signals table"""
        if not self.signals_container:
            return
        
        self.signals_container.clear()
        
        with self.signals_container:
            ui.label(f"Semantic Signals ({len(self.semantic_signals)})").classes("text-xl font-bold mb-4")
            
            if not self.semantic_signals:
                ui.label("No semantic signals available").classes("text-gray-400 italic")
                return
            
            # Group by station
            stations_map = {}
            for signal in self.semantic_signals:
                metadata = signal.get('metadata', {})
                station_id = metadata.get('station_id', 'unknown')
                
                if station_id not in stations_map:
                    stations_map[station_id] = {
                        'metadata': metadata,
                        'signals': []
                    }
                stations_map[station_id]['signals'].append(signal)
            
            # Render each station's signals
            for station_id, station_data in stations_map.items():
                await self.render_station_card(station_id, station_data)
    
    async def render_station_card(self, station_id: str, station_data: Dict[str, Any]):
        """Render a station's semantic signals card"""
        metadata = station_data['metadata']
        signals = station_data['signals']
        
        station_name = metadata.get('station_name', station_id)
        line_id = metadata.get('line_id', 'unknown')
        
        with ui.card().classes("w-full mb-4"):
            # Header
            with ui.row().classes("w-full items-center mb-2"):
                ui.label(f"🏭 {station_name}").classes("text-lg font-bold")
                ui.badge(f"Line: {line_id}").props("color=blue")
                ui.badge(f"{len(signals)} signals").props("color=grey")
            
            # Signals grid
            with ui.grid(columns=2).classes("w-full gap-2"):
                for signal in signals:
                    await self.render_signal_card(signal)
    
    async def render_signal_card(self, signal: Dict[str, Any]):
        """Render individual semantic signal"""
        semantic_id = signal.get('semantic_id', 'unknown')
        value = signal.get('value')
        unit = signal.get('unit', '')
        loss_category = signal.get('loss_category')
        quality = signal.get('quality', 'good')
        
        # Determine card color based on loss_category
        card_class = "p-3 rounded"
        if loss_category:
            if 'availability' in loss_category:
                card_class += " bg-red-50 border-l-4 border-red-500"
            elif 'performance' in loss_category:
                card_class += " bg-yellow-50 border-l-4 border-yellow-500"
            elif 'quality' in loss_category:
                card_class += " bg-orange-50 border-l-4 border-orange-500"
            else:
                card_class += " bg-gray-50 border-l-4 border-gray-400"
        else:
            card_class += " bg-white border"
        
        with ui.element('div').classes(card_class):
            # Semantic ID
            ui.label(semantic_id).classes("text-xs font-mono text-gray-600")
            
            # Value
            value_text = f"{value}"
            if unit:
                value_text += f" {unit}"
            ui.label(value_text).classes("text-lg font-bold")
            
            # Loss category badge
            if loss_category:
                with ui.row().classes("mt-1"):
                    ui.badge(loss_category).props("color=negative")
            
            # Quality indicator
            quality_color = "green" if quality == "good" else "red"
            ui.label(f"● {quality}").classes(f"text-xs text-{quality_color}-500")
    
    async def render_kpis(self):
        """Render derived KPIs"""
        if not self.kpis_container:
            return
        
        self.kpis_container.clear()
        
        with self.kpis_container:
            ui.label(f"Derived KPIs ({len(self.kpis)})").classes("text-xl font-bold mb-4")
            
            if not self.kpis:
                ui.label("No KPIs calculated").classes("text-gray-400 italic")
                return
            
            # Render KPI cards
            with ui.grid(columns=3).classes("w-full gap-4"):
                for kpi in self.kpis:
                    await self.render_kpi_card(kpi)
    
    async def render_kpi_card(self, kpi: Dict[str, Any]):
        """Render individual KPI card"""
        kpi_id = kpi.get('kpi_id', 'unknown')
        value = kpi.get('value', 0)
        unit = kpi.get('unit', '')
        target = kpi.get('target')
        description = kpi.get('description', '')
        
        # Determine if target met
        target_met = True
        if target is not None:
            target_met = value >= target
        
        card_color = "bg-green-50 border-green-500" if target_met else "bg-red-50 border-red-500"
        
        with ui.card().classes(f"{card_color} border-l-4"):
            ui.label(kpi_id).classes("text-sm font-mono text-gray-600")
            
            value_text = f"{value:.1f}"
            if unit:
                value_text += f" {unit}"
            ui.label(value_text).classes("text-2xl font-bold")
            
            if target is not None:
                target_text = f"Target: {target:.1f} {unit}"
                ui.label(target_text).classes("text-xs text-gray-500")
            
            if description:
                ui.label(description).classes("text-xs text-gray-600 mt-1")
    
    async def render_station_details(
        self,
        signals: List[Dict[str, Any]],
        kpis: List[Dict[str, Any]],
        validation: Dict[str, Any]
    ):
        """Render detailed view for selected station"""
        if not self.signals_container:
            return
        
        self.signals_container.clear()
        
        with self.signals_container:
            # Station header
            ui.label(f"Station: {self.selected_station} (Line {self.selected_line})").classes("text-2xl font-bold mb-4")
            
            # Validation status
            is_valid = validation.get('valid', False)
            errors = validation.get('errors', [])
            warnings = validation.get('warnings', [])
            
            if not is_valid:
                with ui.card().classes("bg-red-50 border-red-500 border-l-4 mb-4"):
                    ui.label("❌ Validation Errors").classes("font-bold text-red-700")
                    for error in errors:
                        ui.label(f"• {error}").classes("text-sm text-red-600")
            else:
                with ui.card().classes("bg-green-50 border-green-500 border-l-4 mb-4"):
                    ui.label("✅ Valid Semantic Signals").classes("font-bold text-green-700")
            
            if warnings:
                with ui.card().classes("bg-yellow-50 border-yellow-500 border-l-4 mb-4"):
                    ui.label("⚠️ Warnings").classes("font-bold text-yellow-700")
                    for warning in warnings:
                        ui.label(f"• {warning}").classes("text-sm text-yellow-600")
            
            # Signals
            ui.label("Semantic Signals").classes("text-xl font-bold mt-4 mb-2")
            with ui.grid(columns=2).classes("w-full gap-2"):
                for signal in signals:
                    await self.render_signal_card(signal)
            
            # KPIs
            if kpis:
                ui.label("Derived KPIs").classes("text-xl font-bold mt-4 mb-2")
                with ui.grid(columns=3).classes("w-full gap-4"):
                    for kpi in kpis:
                        await self.render_kpi_card(kpi)
    
    async def render_loss_category_legend(self):
        """Render loss category legend"""
        if not self.loss_category_container:
            return
        
        self.loss_category_container.clear()
        
        with self.loss_category_container:
            ui.label("Loss Categories").classes("text-lg font-bold mb-2")
            
            # Availability
            with ui.expansion("Availability Losses", icon="error").classes("w-full mb-2"):
                categories = self.loss_categories.get('availability', [])
                for cat in categories:
                    with ui.row().classes("items-center"):
                        ui.label("🔴").classes("text-xl")
                        ui.label(cat).classes("text-sm")
            
            # Performance
            with ui.expansion("Performance Losses", icon="speed").classes("w-full mb-2"):
                categories = self.loss_categories.get('performance', [])
                for cat in categories:
                    with ui.row().classes("items-center"):
                        ui.label("🟡").classes("text-xl")
                        ui.label(cat).classes("text-sm")
            
            # Quality
            with ui.expansion("Quality Losses", icon="verified").classes("w-full mb-2"):
                categories = self.loss_categories.get('quality', [])
                for cat in categories:
                    with ui.row().classes("items-center"):
                        ui.label("🟠").classes("text-xl")
                        ui.label(cat).classes("text-sm")
            
            # Non-productive
            with ui.expansion("Non-Productive", icon="info").classes("w-full"):
                categories = self.loss_categories.get('non_productive', [])
                for cat in categories:
                    with ui.row().classes("items-center"):
                        ui.label("⚪").classes("text-xl")
                        ui.label(cat).classes("text-sm")
    
    def render(self):
        """Render the Semantic Signals UI"""
        with ui.column().classes("w-full h-full p-4"):
            # Header
            ui.label("🔀 Semantic Mapping Engine").classes("text-2xl font-bold mb-4")
            ui.label("Raw OPC UA Tags → Stable MES Semantic Signals").classes("text-gray-600 mb-4")
            
            # Control panel
            with ui.card().classes("w-full mb-4"):
                with ui.row().classes("w-full items-center gap-4"):
                    ui.button("Refresh All", on_click=self.load_semantic_signals).props("color=primary icon=refresh")
                    
                    ui.input(
                        label="Line ID",
                        value=self.selected_line,
                        on_change=lambda e: setattr(self, 'selected_line', e.value)
                    ).classes("w-32").props("dense")
                    
                    ui.input(
                        label="Station ID",
                        value=self.selected_station,
                        on_change=lambda e: setattr(self, 'selected_station', e.value)
                    ).classes("w-32").props("dense")
                    
                    ui.button(
                        "Load Station",
                        on_click=self.load_station_signals
                    ).props("color=green icon=search")
            
            # Main layout
            with ui.row().classes("w-full gap-4"):
                # Left: Signals
                with ui.column().classes("w-2/3"):
                    with ui.card().classes("w-full"):
                        self.signals_container = ui.column().classes("w-full")
                        with self.signals_container:
                            ui.label("Loading semantic signals...").classes("text-gray-400 italic")
                    
                    # KPIs below signals
                    with ui.card().classes("w-full mt-4"):
                        self.kpis_container = ui.column().classes("w-full")
                        with self.kpis_container:
                            ui.label("No KPIs calculated yet").classes("text-gray-400 italic")
                
                # Right: Loss Categories Legend
                with ui.column().classes("w-1/3"):
                    with ui.card().classes("w-full"):
                        self.loss_category_container = ui.column().classes("w-full")
        
        # Load data on startup
        asyncio.create_task(self.load_loss_categories())
        asyncio.create_task(self.load_semantic_signals())
        asyncio.create_task(self.render_loss_category_legend())
        
        # Auto-refresh every 5 seconds
        self.refresh_timer = ui.timer(5.0, self.load_semantic_signals)


def render_semantic_signals():
    """Render Semantic Signals screen"""
    screen = SemanticSignalsScreen()
    screen.render()
