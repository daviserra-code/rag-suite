"""
Legacy UI Route - Original 23-tab interface
Kept for safety during migration
"""

from nicegui import ui
from apps.shopfloor_copilot.ui import build_ui as build_legacy_ui
from apps.shopfloor_copilot.theme import apply_shopfloor_theme


@ui.page('/legacy')
def legacy_page():
    """
    Legacy 23-tab interface
    This route renders the original horizontal tabs UI
    """
    
    apply_shopfloor_theme()
    
    # Info card at top
    with ui.card().classes('w-full bg-yellow-100 border-l-4 border-yellow-500 mb-4'):
        with ui.row().classes('items-center gap-3 p-2'):
            ui.icon('info').classes('text-yellow-700 text-2xl')
            with ui.column().classes('flex-1'):
                ui.label('You are using the legacy 23-tab interface').classes('font-medium text-yellow-900')
                ui.label('Switch to the new tile-based navigation for a better experience').classes('text-sm text-yellow-800')
            ui.button('New UI', icon='home', on_click=lambda: ui.navigate.to('/')).props('flat color=yellow-900')
    
    # Render original UI
    build_legacy_ui()
