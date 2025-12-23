"""
Diagnostics Explainer Screen
Sprint 3 — AI-Grounded Diagnostics & Explainability

UI for requesting and displaying AI-grounded, explainable diagnostics.
"""

import asyncio
from nicegui import ui
import httpx
import logging

logger = logging.getLogger(__name__)

# API URL
SHOPFLOOR_API = "http://localhost:8010"


class DiagnosticsExplainerScreen:
    """
    UI screen for AI-grounded diagnostics.
    
    Features:
    - Scope selector (line or station)
    - Equipment ID input
    - "Explain this situation" button
    - 4-section structured output panel
    """
    
    def __init__(self):
        self.scope = "station"
        self.equipment_id = ""
        self.diagnostic_result = None
        self.loading = False
        
    def render(self):
        """Render the diagnostics explainer screen."""
        
        with ui.column().classes('w-full gap-4 p-4'):
            # Header
            ui.label('AI Diagnostics — Explainable Root Cause Analysis').classes('text-2xl font-bold')
            ui.label('Sprint 3: Grounded in semantic signals, loss categories, and RAG knowledge').classes('text-gray-600')
            
            ui.separator()
            
            # Input Section
            with ui.card().classes('w-full'):
                ui.label('Diagnostic Request').classes('text-xl font-semibold mb-2')
                
                with ui.row().classes('w-full gap-4 items-end'):
                    # Scope selector
                    with ui.column().classes('flex-none'):
                        ui.label('Scope').classes('text-sm font-medium mb-1')
                        scope_select = ui.select(
                            ['station', 'line'],
                            value='station',
                            on_change=lambda e: self._on_scope_change(e.value)
                        ).classes('w-32')
                    
                    # Equipment ID input
                    with ui.column().classes('flex-1'):
                        ui.label('Equipment ID').classes('text-sm font-medium mb-1')
                        self.equipment_input = ui.input(
                            placeholder='e.g., ST18 or A01',
                            value=''
                        ).classes('w-full').on('input', lambda e: self._on_equipment_change(e.value))
                    
                    # Explain button
                    explain_button = ui.button(
                        'Explain this situation',
                        on_click=self._explain_situation,
                        icon='psychology'
                    ).props('color=primary')
            
            # Loading indicator
            self.loading_card = ui.card().classes('w-full hidden')
            with self.loading_card:
                with ui.row().classes('items-center gap-4'):
                    ui.spinner(size='lg', color='primary')
                    ui.label('Analyzing runtime data and generating explanation...').classes('text-lg')
            
            # Output Section (4 sections)
            self.output_container = ui.column().classes('w-full gap-4 hidden')
            
            with self.output_container:
                ui.label('Diagnostic Explanation').classes('text-xl font-semibold mt-4')
                
                # Section 1: What is happening (Runtime Evidence)
                with ui.expansion('Section 1 — What is happening', icon='fact_check').classes('w-full bg-blue-50').props('default-opened'):
                    with ui.card().classes('w-full bg-white'):
                        ui.label('Runtime Evidence (Facts Only)').classes('text-sm font-medium text-gray-600 mb-2')
                        self.section1_content = ui.markdown('*No diagnostic generated yet*')
                
                # Section 2: Why this is happening (Reasoned Explanation)
                with ui.expansion('Section 2 — Why this is happening', icon='lightbulb').classes('w-full bg-yellow-50').props('default-opened'):
                    with ui.card().classes('w-full bg-white'):
                        ui.label('Reasoned Explanation').classes('text-sm font-medium text-gray-600 mb-2')
                        self.section2_content = ui.markdown('*No diagnostic generated yet*')
                
                # Section 3: What to do now (Procedures)
                with ui.expansion('Section 3 — What to do now', icon='build').classes('w-full bg-green-50').props('default-opened'):
                    with ui.card().classes('w-full bg-white'):
                        ui.label('Procedures (from RAG)').classes('text-sm font-medium text-gray-600 mb-2')
                        self.section3_content = ui.markdown('*No diagnostic generated yet*')
                
                # Section 4: What to check next (Checklist)
                with ui.expansion('Section 4 — What to check next', icon='checklist').classes('w-full bg-purple-50').props('default-opened'):
                    with ui.card().classes('w-full bg-white'):
                        ui.label('Actionable Checklist').classes('text-sm font-medium text-gray-600 mb-2')
                        self.section4_content = ui.markdown('*No diagnostic generated yet*')
                
                # Metadata
                with ui.card().classes('w-full bg-gray-50 mt-4'):
                    ui.label('Diagnostic Metadata').classes('text-sm font-semibold mb-2')
                    self.metadata_content = ui.column().classes('text-xs text-gray-700')
            
            # Examples
            with ui.card().classes('w-full bg-gray-50 mt-4'):
                ui.label('Examples').classes('text-sm font-semibold mb-2')
                with ui.row().classes('gap-2'):
                    ui.button(
                        'Station ST18',
                        on_click=lambda: self._load_example('station', 'ST18'),
                        icon='analytics'
                    ).props('size=sm outline')
                    ui.button(
                        'Station ST20',
                        on_click=lambda: self._load_example('station', 'ST20'),
                        icon='analytics'
                    ).props('size=sm outline')
                    ui.button(
                        'Line A01',
                        on_click=lambda: self._load_example('line', 'A01'),
                        icon='view_list'
                    ).props('size=sm outline')
                    ui.button(
                        'Line B01',
                        on_click=lambda: self._load_example('line', 'B01'),
                        icon='view_list'
                    ).props('size=sm outline')
    
    def _on_scope_change(self, value):
        """Handle scope selection change."""
        self.scope = value
    
    def _on_equipment_change(self, value):
        """Handle equipment ID input change."""
        self.equipment_id = value.strip()
    
    def _load_example(self, scope, equipment_id):
        """Load an example diagnostic request."""
        self.scope = scope
        self.equipment_id = equipment_id
        # Update the input field value
        if hasattr(self, 'equipment_input'):
            self.equipment_input.value = equipment_id
        self._explain_situation()
    
    async def _explain_situation(self):
        """Request diagnostic explanation from API."""
        if not self.equipment_id:
            ui.notify('Please enter an equipment ID', type='warning')
            return
        
        try:
            # Show loading
            self.loading_card.classes(remove='hidden')
            self.output_container.classes(add='hidden')
            
            # Call API
            logger.info(f"Requesting diagnostic: {self.scope} {self.equipment_id}")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{SHOPFLOOR_API}/api/diagnostics/explain",
                    json={
                        "scope": self.scope,
                        "id": self.equipment_id
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self._display_diagnostic(result)
                    ui.notify('Diagnostic generated successfully', type='positive')
                else:
                    error_detail = response.json().get('detail', 'Unknown error')
                    ui.notify(f'Error: {error_detail}', type='negative')
                    logger.error(f"Diagnostic API error: {response.status_code} - {error_detail}")
        
        except Exception as e:
            ui.notify(f'Failed to generate diagnostic: {str(e)}', type='negative')
            logger.error(f"Diagnostic request failed: {e}", exc_info=True)
        
        finally:
            # Hide loading
            self.loading_card.classes(add='hidden')
    
    def _display_diagnostic(self, result: dict):
        """Display diagnostic result in the UI."""
        # Update sections
        self.section1_content.content = result.get('what_is_happening', '*No data*')
        self.section2_content.content = result.get('why_this_is_happening', '*No data*')
        self.section3_content.content = result.get('what_to_do_now', '*No data*')
        self.section4_content.content = result.get('what_to_check_next', '*No data*')
        
        # Update metadata
        self.metadata_content.clear()
        with self.metadata_content:
            metadata = result.get('metadata', {})
            ui.label(f"Equipment: {result.get('scope', 'unknown')} {result.get('equipment_id', 'unknown')}")
            ui.label(f"Plant: {metadata.get('plant', 'Unknown')}")
            ui.label(f"Timestamp: {metadata.get('timestamp', 'Unknown')}")
            ui.label(f"Model: {metadata.get('model', 'Unknown')}")
            
            loss_categories = metadata.get('loss_categories', [])
            if loss_categories:
                ui.label(f"Active Loss Categories: {', '.join(loss_categories)}")
            else:
                ui.label("Active Loss Categories: None detected")
            
            ui.label(f"RAG Documents Retrieved: {metadata.get('rag_documents', 0)}")
        
        # Show output
        self.output_container.classes(remove='hidden')


def render_diagnostics_explainer():
    """Render the diagnostics explainer screen."""
    screen = DiagnosticsExplainerScreen()
    screen.render()
