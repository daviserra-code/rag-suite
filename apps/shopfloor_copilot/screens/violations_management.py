"""
Violations Management Screen
Displays active and historical violations with lifecycle management
"""
from nicegui import ui
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import os


SHOPFLOOR_API = os.getenv("SHOPFLOOR_API", "http://localhost:8010")


class ViolationsManagementScreen:
    """Violations lifecycle management UI"""
    
    def __init__(self):
        self.active_violations: List[Dict[str, Any]] = []
        self.historical_violations: List[Dict[str, Any]] = []
        self.selected_violation: Optional[Dict[str, Any]] = None
        self.timeline_data: Optional[Dict[str, Any]] = None
        
        # UI components
        self.active_table: Optional[ui.column] = None
        self.history_table: Optional[ui.column] = None
        self.timeline_panel: Optional[ui.column] = None
        self.details_panel: Optional[ui.column] = None
        
    async def load_active_violations(self):
        """Load active violations from API"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{SHOPFLOOR_API}/api/violations/active")
                data = response.json()
                
                if data.get("ok"):
                    self.active_violations = data.get("violations", [])
                    await self.render_active_table()
        except Exception as e:
            print(f"[ERROR] Failed to load active violations: {str(e)}")
    
    async def load_historical_violations(self):
        """Load historical violations from API"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{SHOPFLOOR_API}/api/violations/history")
                data = response.json()
                
                if data.get("ok"):
                    self.historical_violations = data.get("violations", [])
                    await self.render_history_table()
        except Exception as e:
            print(f"[ERROR] Failed to load historical violations: {str(e)}")
    
    async def load_violation_timeline(self, violation_id: str):
        """Load full timeline for a specific violation"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{SHOPFLOOR_API}/api/violations/{violation_id}/timeline")
                data = response.json()
                
                if data.get("ok"):
                    self.timeline_data = data
                    if self.timeline_panel:
                        await self.render_timeline()
                    else:
                        print("[WARNING] Timeline panel not initialized")
                else:
                    print(f"[ERROR] Timeline API returned error: {data}")
        except Exception as e:
            print(f"[ERROR] Failed to load timeline: {str(e)}")
            raise
    
    async def acknowledge_violation(self, violation_id: str):
        """Acknowledge a violation"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{SHOPFLOOR_API}/api/violations/{violation_id}/ack",
                    json={
                        "ack_type": "acknowledged",
                        "ack_by": "operator",
                        "comment": "Acknowledged via UI"
                    }
                )
                data = response.json()
                
                if data.get("ok"):
                    ui.notify("Violation acknowledged", type="positive")
                    await self.load_active_violations()
                    await self.load_violation_timeline(violation_id)
        except Exception as e:
            ui.notify(f"Failed to acknowledge: {str(e)}", type="negative")
    
    async def justify_violation(self, violation_id: str, comment: str, evidence_ref: str = ""):
        """Justify a violation with comment and evidence"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{SHOPFLOOR_API}/api/violations/{violation_id}/ack",
                    json={
                        "ack_type": "justified",
                        "ack_by": "supervisor",
                        "comment": comment,
                        "evidence_ref": evidence_ref
                    }
                )
                data = response.json()
                
                if data.get("ok"):
                    ui.notify("Violation justified", type="positive")
                    await self.load_active_violations()
                    await self.load_violation_timeline(violation_id)
        except Exception as e:
            ui.notify(f"Failed to justify: {str(e)}", type="negative")
    
    async def resolve_violation(self, violation_id: str, comment: str = ""):
        """Resolve a violation"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{SHOPFLOOR_API}/api/violations/{violation_id}/resolve",
                    json={
                        "ack_by": "operator",
                        "comment": comment
                    }
                )
                data = response.json()
                
                if data.get("ok"):
                    ui.notify("Violation resolved", type="positive")
                    await self.load_active_violations()
                    await self.load_historical_violations()
        except Exception as e:
            ui.notify(f"Failed to resolve: {str(e)}", type="negative")
    
    def render(self):
        """Render the violations management screen"""
        with ui.column().classes('w-full gap-4 p-4'):
            # Header
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.label('Violations Management').classes('text-2xl font-bold text-white')
                ui.button('Refresh', icon='refresh', on_click=self.refresh_all).props('color=primary')
            
            # Tabs for Active vs Historical
            with ui.tabs().classes('w-full') as tabs:
                tab_active = ui.tab('Active Violations', icon='warning')
                tab_history = ui.tab('Historical', icon='history')
            
            with ui.tab_panels(tabs, value=tab_active).classes('w-full'):
                # Active violations tab
                with ui.tab_panel(tab_active):
                    with ui.row().classes('w-full gap-4'):
                        # Left: Active violations table
                        with ui.column().classes('w-2/3'):
                            ui.label('Active Violations').classes('text-xl font-semibold mb-2')
                            self.active_table = ui.column().classes('w-full')
                        
                        # Right: Details and timeline
                        with ui.column().classes('w-1/3'):
                            ui.label('Violation Details').classes('text-xl font-semibold mb-2')
                            self.details_panel = ui.column().classes('w-full')
                            
                            ui.label('Timeline').classes('text-xl font-semibold mt-4 mb-2')
                            self.timeline_panel = ui.column().classes('w-full')
                
                # Historical violations tab
                with ui.tab_panel(tab_history):
                    ui.label('Historical Violations').classes('text-xl font-semibold mb-2')
                    self.history_table = ui.column().classes('w-full')
            
            # Load data
            asyncio.create_task(self.load_active_violations())
            asyncio.create_task(self.load_historical_violations())
    
    async def render_active_table(self):
        """Render active violations table"""
        if not self.active_table:
            return
        
        self.active_table.clear()
        
        with self.active_table:
            if not self.active_violations:
                ui.label('No active violations').classes('text-gray-300 italic')
                return
            
            for violation in self.active_violations:
                await self.render_violation_card(violation, is_active=True)
    
    async def render_history_table(self):
        """Render historical violations table"""
        if not self.history_table:
            return
        
        self.history_table.clear()
        
        with self.history_table:
            if not self.historical_violations:
                ui.label('No historical violations').classes('text-gray-300 italic')
                return
            
            for violation in self.historical_violations:
                await self.render_violation_card(violation, is_active=False)
    
    async def render_violation_card(self, violation: Dict[str, Any], is_active: bool):
        """Render a single violation card"""
        violation_id = violation.get('id')
        station = violation.get('station', 'Unknown')
        profile = violation.get('profile', 'Unknown')
        severity = violation.get('severity', 'unknown')
        state = violation.get('state', 'OPEN')
        ts_start = violation.get('ts_start', '')
        
        # Color based on severity and state - dark theme
        if severity == 'critical':
            card_color = 'bg-red-900 border-l-4 border-red-500'
            severity_badge = 'red'
        elif severity == 'warning':
            card_color = 'bg-yellow-900 border-l-4 border-yellow-500'
            severity_badge = 'orange'
        else:
            card_color = 'bg-blue-900 border-l-4 border-blue-500'
            severity_badge = 'blue'
        
        # State badge color
        state_colors = {
            'OPEN': 'red',
            'ACKNOWLEDGED': 'orange',
            'JUSTIFIED': 'yellow',
            'RESOLVED': 'green'
        }
        state_color = state_colors.get(state, 'grey')
        
        with ui.card().classes(f'w-full {card_color} p-3 mb-2 cursor-pointer hover:shadow-lg'):
            with ui.row().classes('w-full items-center justify-between'):
                # Left: Station and severity
                with ui.column().classes('gap-1'):
                    with ui.row().classes('items-center gap-2'):
                        ui.badge(station).props(f'color=primary')
                        ui.badge(severity.upper()).props(f'color={severity_badge}')
                        ui.badge(state).props(f'color={state_color}')
                    ui.label(f'Profile: {profile}').classes('text-sm text-gray-200')
                    ui.label(f'Started: {ts_start[:19] if ts_start else "Unknown"}').classes('text-xs text-gray-300')
                
                # Right: Action buttons
                if is_active:
                    with ui.row().classes('gap-2'):
                        # Create handler with immediate feedback
                        async def handle_view(vid=violation_id):
                            await ui.run_javascript('console.log("View clicked for: ' + vid + '")')
                            await self.view_violation(vid)
                        
                        async def handle_ack(vid=violation_id):
                            await ui.run_javascript('console.log("Acknowledge clicked for: ' + vid + '")')
                            await self.acknowledge_violation(vid)
                        
                        ui.button('View', icon='visibility', on_click=handle_view).props('size=sm outline')
                        if state == 'OPEN':
                            ui.button('Acknowledge', icon='check', on_click=handle_ack).props('size=sm color=orange')
                        if state == 'ACKNOWLEDGED':
                            ui.button('Justify', icon='note_add', on_click=lambda v_id=violation_id: self.show_justify_dialog(v_id)).props('size=sm color=yellow')
                        ui.button('Resolve', icon='done_all', on_click=lambda v_id=violation_id: self.show_resolve_dialog(v_id)).props('size=sm color=green')
    
    async def view_violation(self, violation_id: str):
        """View violation details and timeline"""
        print(f"[INFO] Loading timeline for violation {violation_id}")
        try:
            await self.load_violation_timeline(violation_id)
            if self.timeline_data:
                print(f"[INFO] Timeline loaded successfully")
            else:
                print(f"[WARNING] No timeline data available")
        except Exception as e:
            print(f"[ERROR] Failed to load timeline: {str(e)}")
    
    def show_justify_dialog(self, violation_id: str):
        """Show dialog to justify a violation"""
        with ui.dialog() as dialog, ui.card():
            ui.label('Justify Violation').classes('text-xl font-bold mb-4')
            
            comment_input = ui.textarea('Comment (required)', placeholder='Explain why this is acceptable...').classes('w-full')
            evidence_input = ui.input('Evidence Reference', placeholder='DEV-2025-042, WO-12345, etc.').classes('w-full')
            
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Justify', on_click=lambda: self.submit_justification(violation_id, comment_input.value, evidence_input.value, dialog)).props('color=primary')
        
        dialog.open()
    
    async def submit_justification(self, violation_id: str, comment: str, evidence_ref: str, dialog):
        """Submit justification"""
        if not comment.strip():
            ui.notify('Comment is required for justification', type='warning')
            return
        
        await self.justify_violation(violation_id, comment, evidence_ref)
        dialog.close()
    
    def show_resolve_dialog(self, violation_id: str):
        """Show dialog to resolve a violation"""
        with ui.dialog() as dialog, ui.card():
            ui.label('Resolve Violation').classes('text-xl font-bold mb-4')
            
            comment_input = ui.textarea('Resolution Comment (optional)', placeholder='Describe how the issue was fixed...').classes('w-full')
            
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Resolve', on_click=lambda: self.submit_resolution(violation_id, comment_input.value, dialog)).props('color=green')
        
        dialog.open()
    
    async def submit_resolution(self, violation_id: str, comment: str, dialog):
        """Submit resolution"""
        await self.resolve_violation(violation_id, comment)
        dialog.close()
    
    async def render_timeline(self):
        """Render violation timeline"""
        if not self.timeline_panel or not self.timeline_data:
            return
        
        self.timeline_panel.clear()
        
        with self.timeline_panel:
            violation = self.timeline_data.get('violation', {})
            acknowledgments = self.timeline_data.get('acknowledgments', [])
            
            # Violation info - dark theme
            with ui.card().classes('w-full bg-gray-800 p-3 mb-2'):
                ui.label('Violation Created').classes('font-semibold text-white')
                ui.label(f"{violation.get('ts_start', '')[:19]}").classes('text-sm text-gray-300')
            
            # Acknowledgments
            for ack in acknowledgments:
                ack_type = ack.get('ack_type', 'acknowledged')
                ack_by = ack.get('ack_by', 'Unknown')
                ts = ack.get('ts', '')
                comment = ack.get('comment', '')
                
                # Color based on ack type - dark theme variants
                if ack_type == 'resolved':
                    color = 'bg-green-900 border-l-4 border-green-500'
                elif ack_type == 'justified':
                    color = 'bg-yellow-900 border-l-4 border-yellow-500'
                else:
                    color = 'bg-blue-900 border-l-4 border-blue-500'
                
                with ui.card().classes(f'w-full {color} p-3 mb-2'):
                    ui.label(ack_type.upper()).classes('font-semibold text-white')
                    ui.label(f'By: {ack_by}').classes('text-sm text-gray-200')
                    ui.label(f'{ts[:19]}').classes('text-xs text-gray-300')
                    if comment:
                        ui.label(f'"{comment}"').classes('text-sm italic mt-1 text-gray-100')
    
    async def refresh_all(self):
        """Refresh all data"""
        await self.load_active_violations()
        await self.load_historical_violations()


def render_violations_management():
    """Render the violations management screen"""
    screen = ViolationsManagementScreen()
    screen.render()
