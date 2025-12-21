"""
OPC Explorer Page - Sprint 1: UAExpert-like browser
"""

from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.opc_explorer import render_opc_explorer as render_opc_explorer_screen
from apps.shopfloor_copilot.theme import apply_shopfloor_theme


@ui.page('/connectivity/opc-explorer')
def opc_explorer_page():
    """OPC Explorer page route"""
    
    apply_shopfloor_theme()
    
    # Create layout shell
    content = layout_shell(
        title="OPC Explorer",
        show_drawer=True,
        theme="legacy"
    )
    
    # Render page content
    with content:
        create_page_header(
            title="OPC Explorer",
            subtitle="Sprint 1: UAExpert-like OPC UA browser",
            icon="explore",
            theme="legacy"
        )
        
        # Render the existing OPC Explorer screen
        render_opc_explorer_screen()
