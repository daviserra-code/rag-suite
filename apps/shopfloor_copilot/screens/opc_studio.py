"""
OPC Studio Tab - Phase B Implementation

Shows live OPC Studio status, plant model, snapshot viewer, and scenario builder.
Enables operators to monitor and apply scenarios to the simulated plant.
"""

import os
import httpx
from nicegui import ui
from datetime import datetime

# NiceGUI async functions run server-side, so use Docker internal hostname
OPC_STUDIO_URL = os.getenv("OPC_STUDIO_URL", "http://opc-studio:8040")


async def fetch_opc_health():
    """Fetch OPC Studio health status"""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{OPC_STUDIO_URL}/health")
            return r.json() if r.status_code == 200 else {"status": "error", "message": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def fetch_historian_status():
    """Fetch historian status"""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{OPC_STUDIO_URL}/historian/status")
            return r.json() if r.status_code == 200 else {"enabled": False, "message": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"enabled": False, "message": str(e)}


async def fetch_plant_model():
    """Fetch plant model structure"""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{OPC_STUDIO_URL}/model")
            return r.json() if r.status_code == 200 else {"plants": [], "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"plants": [], "error": str(e)}


async def fetch_snapshot():
    """Fetch current plant snapshot"""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{OPC_STUDIO_URL}/snapshot")
            return r.json() if r.status_code == 200 else {"snapshot": {}, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"snapshot": {}, "error": str(e)}


async def apply_scenario(line_id: str, station_id: str, event: str, duration_min: int, impact: dict):
    """Apply a scenario to OPC Studio"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            payload = {
                "line": line_id,
                "station": station_id,
                "event": event,
                "duration_min": duration_min,
                "impact": impact
            }
            r = await client.post(f"{OPC_STUDIO_URL}/scenario/apply", json=payload)
            if r.status_code == 200:
                result = r.json()
                return {"success": result.get("ok", False), "message": f"Applied: {event}", "data": result}
            else:
                return {"success": False, "message": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def opc_studio_screen():
    """Build the OPC Studio tab UI"""
    
    ui.label('OPC Studio Control Panel').classes('text-2xl font-bold mb-4')
    ui.label('Monitor and control the OPC UA simulation and historian').classes('text-gray-600 mb-6')
    
    # Status Panel
    with ui.card().classes('w-full mb-4'):
        ui.label('🔍 Status Panel').classes('text-lg font-semibold mb-2')
        
        status_container = ui.row().classes('gap-4 w-full')
        
        async def refresh_status():
            status_container.clear()
            with status_container:
                # OPC Health
                health = await fetch_opc_health()
                # Health endpoint returns {"ok": true, ...} or {"status": "error", ...}
                if health.get("ok"):
                    status = "ok"
                    color = "green"
                else:
                    status = health.get("status", "unknown")
                    color = "red"
                ui.badge(f"OPC Studio: {status.upper()}", color=color).classes('text-lg')
                if not health.get("ok") and "message" in health:
                    ui.label(f"Error: {health['message']}").classes('text-sm text-red-600')
                
                # Historian Status
                historian = await fetch_historian_status()
                h_status = "ENABLED" if historian.get("enabled") else "DISABLED"
                h_color = "blue" if historian.get("enabled") else "gray"
                ui.badge(f"Historian: {h_status}", color=h_color).classes('text-lg')
                
                if historian.get("enabled"):
                    interval = historian.get("interval_s", "?")
                    ui.label(f"(Interval: {interval}s)").classes('text-sm text-gray-600')
        
        ui.button('Refresh Status', on_click=refresh_status, icon='refresh').classes('mt-2')
    
    # Model Browser
    with ui.card().classes('w-full mb-4'):
        ui.label('🏭 Plant Model Browser').classes('text-lg font-semibold mb-2')
        
        model_container = ui.column().classes('w-full')
        
        async def load_model():
            model_container.clear()
            with model_container:
                response = await fetch_plant_model()
                
                if "error" in response:
                    ui.label(f"❌ Error: {response['error']}").classes('text-red-600')
                    return
                
                # API returns {"ok": true, "model": {"plant": "TORINO", "plant_name": "...", "lines": [...]}}
                model = response.get("model", {})
                plant_id = model.get("plant")
                plant_name = model.get("plant_name", plant_id)
                location = model.get("location", "")
                lines = model.get("lines", [])
                
                if not plant_id:
                    ui.label("No plant loaded").classes('text-gray-600')
                    return
                
                # Plant header with metadata
                with ui.expansion(f"Plant: {plant_id} - {plant_name}", icon='factory', value=True).classes('w-full'):
                    if location:
                        ui.label(f"📍 Location: {location}").classes('text-sm text-gray-600 mb-2')
                    ui.label(f"📊 Total Lines: {len(lines)}").classes('text-sm font-semibold mb-3')
                    
                    for line in lines:
                        line_name = line.get("name", line['id'])
                        line_type = line.get("type", "unknown")
                        product_family = line.get("product_family", "")
                        stations = line.get("stations", [])
                        
                        with ui.expansion(f"{line['id']}: {line_name}", icon='conveyor_belt').classes('ml-4 mt-2'):
                            # Line metadata
                            ui.label(f"Type: {line_type}").classes('text-sm text-gray-700')
                            if product_family:
                                ui.label(f"Product Family: {product_family}").classes('text-sm text-gray-700')
                            ui.label(f"Stations: {len(stations)}").classes('text-sm font-semibold mt-1 mb-2')
                            
                            # Station grid with enriched metadata
                            if stations:
                                with ui.grid(columns=2).classes('gap-2 mt-2 w-full'):
                                    for station in stations:
                                        station_id = station.get("id", station) if isinstance(station, dict) else station
                                        station_name = station.get("name", station_id) if isinstance(station, dict) else station_id
                                        station_type = station.get("type", "") if isinstance(station, dict) else ""
                                        is_critical = station.get("critical", False) if isinstance(station, dict) else False
                                        
                                        badge_color = 'red' if is_critical else 'indigo'
                                        badge_icon = '⚠️' if is_critical else '🔧'
                                        
                                        with ui.card().classes('p-2 bg-blue-50'):
                                            ui.label(f"{badge_icon} {station_id}").classes('font-semibold text-sm')
                                            if station_name != station_id:
                                                ui.label(station_name).classes('text-xs text-gray-700')
                                            if station_type:
                                                ui.badge(station_type, color=badge_color).classes('text-xs mt-1')
                            else:
                                ui.label("No stations").classes('text-gray-500 text-sm')
        
        ui.button('Load Model', on_click=load_model, icon='download').classes('mt-2')
    
    # Live Snapshot Viewer
    with ui.card().classes('w-full mb-4'):
        ui.label('📊 Live Snapshot Viewer').classes('text-lg font-semibold mb-2')
        
        snapshot_container = ui.column().classes('w-full')
        
        async def refresh_snapshot():
            snapshot_container.clear()
            with snapshot_container:
                response = await fetch_snapshot()
                
                if "error" in response:
                    ui.label(f"❌ Error: {response['error']}").classes('text-red-600')
                    return
                
                # API returns {"ok": true, "data": {"plant": "TORINO", "lines": {"A01": {...}}}}
                snapshot_data = response.get("data", {})
                plant_id = snapshot_data.get("plant", "N/A")
                lines_dict = snapshot_data.get("lines", {})
                
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ui.label(f"⏱️ Snapshot at: {timestamp} | Plant: {plant_id}").classes('text-sm text-gray-600 mb-2')
                
                if not lines_dict:
                    ui.label("No snapshot data available").classes('text-gray-600')
                    return
                
                # Lines table - convert dict to list
                line_cols = [
                    {'name': 'line_id', 'label': 'Line', 'field': 'line_id'},
                    {'name': 'status', 'label': 'Status', 'field': 'status'},
                    {'name': 'oee', 'label': 'OEE', 'field': 'oee'},
                    {'name': 'availability', 'label': 'Availability', 'field': 'availability'},
                    {'name': 'performance', 'label': 'Performance', 'field': 'performance'},
                    {'name': 'quality', 'label': 'Quality', 'field': 'quality'},
                ]
                
                line_rows = []
                all_stations = []
                
                for line_id, line_data in lines_dict.items():
                    line_rows.append({
                        'line_id': line_id,
                        'status': line_data.get('status', 'UNKNOWN'),
                        'oee': f"{line_data.get('oee', 0):.2%}",
                        'availability': f"{line_data.get('availability', 0):.2%}",
                        'performance': f"{line_data.get('performance', 0):.2%}",
                        'quality': f"{line_data.get('quality', 0):.2%}",
                    })
                    
                    # Stations - also a dict
                    stations_dict = line_data.get('stations', {})
                    for station_id, station_data in stations_dict.items():
                        all_stations.append({
                            'line_id': line_id,
                            'station_id': station_id,
                            'state': station_data.get('state', 'UNKNOWN'),
                            'cycle_time': f"{station_data.get('cycle_time_s', 0):.1f}s",
                            'good_count': station_data.get('good_count', 0),
                            'scrap_count': station_data.get('scrap_count', 0),
                        })
                
                ui.label('Lines Status:').classes('font-semibold mt-2')
                ui.table(columns=line_cols, rows=line_rows, row_key='line_id').classes('w-full')
                
                if all_stations:
                    station_cols = [
                        {'name': 'line_id', 'label': 'Line', 'field': 'line_id'},
                        {'name': 'station_id', 'label': 'Station', 'field': 'station_id'},
                        {'name': 'state', 'label': 'State', 'field': 'state'},
                        {'name': 'cycle_time', 'label': 'Cycle Time', 'field': 'cycle_time'},
                        {'name': 'good_count', 'label': 'Good', 'field': 'good_count'},
                        {'name': 'scrap_count', 'label': 'Scrap', 'field': 'scrap_count'},
                    ]
                    
                    ui.label('Stations Status:').classes('font-semibold mt-4')
                    ui.table(columns=station_cols, rows=all_stations, row_key='station_id').classes('w-full')
        
        ui.button('Refresh Snapshot', on_click=refresh_snapshot, icon='refresh').classes('mt-2')
    
    # Scenario Builder (Template-Based)
    with ui.card().classes('w-full mb-4'):
        ui.label('🎬 Scenario Builder').classes('text-lg font-semibold mb-2')
        ui.label('Apply realistic scenario templates with cascading impacts').classes('text-sm text-gray-600 mb-2')
        
        # Fetch templates
        templates_data = []
        try:
            async def fetch_templates():
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{OPC_STUDIO_URL}/scenario/templates", timeout=5.0)
                    return response.json() if response.status_code == 200 else {"templates": []}
            
            # Note: This will be populated when the card loads
            templates_container = ui.column().classes('w-full')
        except Exception as e:
            ui.label(f"⚠️ Template loading error: {str(e)}").classes('text-orange-600 text-sm')
        
        with ui.row().classes('gap-4 w-full mt-3'):
            line_input = ui.input('Line ID', placeholder='A01', value='A01').classes('flex-1')
            station_input = ui.input('Station ID', placeholder='ST18', value='ST18').classes('flex-1')
        
        # Template selection
        template_select = ui.select([], label='Scenario Template', with_input=True).classes('w-full mt-2')
        
        # Severity selection
        severity_select = ui.select(
            ['minor', 'moderate', 'major', 'critical'],
            label='Severity Override (optional)',
            value='moderate'
        ).classes('w-full mt-2')
        
        # Template details display
        template_details = ui.label('').classes('text-sm text-gray-600 mt-2 mb-2')
        
        result_label = ui.label('').classes('mt-2')
        
        async def load_templates():
            try:
                data = await fetch_templates()
                templates_list = data.get("templates", [])
                
                # Build options for select
                options = {}
                for t in templates_list:
                    label = f"{t['name']} ({t['severity']}) - {t.get('duration_min', 0)}min"
                    options[t['id']] = label
                
                template_select.options = options
                if options:
                    first_key = list(options.keys())[0]
                    template_select.value = first_key
                    update_template_details()
                
                return templates_list
            except Exception as e:
                template_details.text = f"❌ Failed to load templates: {str(e)}"
        
        def update_template_details():
            if not template_select.value:
                template_details.text = ""
                return
            
            # Find selected template
            # Note: Would need to store templates_data globally or refetch
            template_details.text = f"Template: {template_select.value} | Severity: {severity_select.value} | Cascading impacts will be applied automatically"
        
        template_select.on('update:model-value', lambda: update_template_details())
        severity_select.on('update:model-value', lambda: update_template_details())
        
        async def apply_template_scenario():
            result_label.text = '⏳ Applying template scenario...'
            result_label.classes('text-blue-600')
            
            try:
                payload = {
                    "line": line_input.value or "A01",
                    "station": station_input.value or "ST18",
                    "template_id": template_select.value,
                    "severity": severity_select.value
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{OPC_STUDIO_URL}/scenario/apply",
                        json=payload,
                        timeout=10.0
                    )
                    result = response.json() if response.status_code == 200 else {"ok": False, "error": "Request failed"}
                
                if result.get("ok"):
                    template_info = result.get("template_applied", {})
                    cascading = "✨ with cascading effects" if template_info.get("cascading") else ""
                    result_label.text = f"✅ Applied: {template_info.get('name', '')} ({template_info.get('severity', '')}) {cascading}"
                    result_label.classes('text-green-600')
                else:
                    result_label.text = f"❌ Failed: {result.get('error', 'Unknown error')}"
                    result_label.classes('text-red-600')
            
            except Exception as e:
                result_label.text = f"❌ Error: {str(e)}"
                result_label.classes('text-red-600')
        
        ui.button('Load Templates', on_click=load_templates, icon='download').classes('mt-2 bg-blue-600')
        ui.button('Apply Template Scenario', on_click=apply_template_scenario, icon='play_arrow').classes('mt-2 bg-green-600')
    
    # Send to Copilot
    with ui.card().classes('w-full mb-4'):
        ui.label('💬 Send Snapshot to AI Copilot').classes('text-lg font-semibold mb-2')
        ui.label('Fetch current snapshot and use it in chat context').classes('text-sm text-gray-600 mb-4')
        
        copilot_result = ui.label('').classes('mt-2')
        
        async def send_to_copilot():
            copilot_result.text = '⏳ Fetching snapshot...'
            data = await fetch_snapshot()
            
            if "error" in data:
                copilot_result.text = f"❌ Error: {data['error']}"
                copilot_result.classes('text-red-600')
                return
            
            # Format snapshot for display
            snapshot = data.get("snapshot", {})
            timestamp = snapshot.get("timestamp", "N/A")
            plant_id = snapshot.get("plant", {}).get("plant_id", "N/A")
            lines_count = len(snapshot.get("plant", {}).get("lines", []))
            
            copilot_result.text = f"✅ Snapshot captured at {timestamp}\nPlant: {plant_id}, Lines: {lines_count}\n\n(In production: this would prefill the chat context)"
            copilot_result.classes('text-green-600')
        
        ui.button('Send to Copilot', on_click=send_to_copilot, icon='chat').classes('bg-blue-600')
