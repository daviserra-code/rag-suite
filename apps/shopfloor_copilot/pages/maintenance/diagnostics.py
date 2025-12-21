"""
AI Diagnostics Page - Sprint 3: Explainable diagnostics
"""

from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.diagnostics_explainer import render_diagnostics_explainer as render_diagnostics_screen
from apps.shopfloor_copilot.theme import apply_shopfloor_theme


@ui.page('/maintenance/diagnostics')
def diagnostics_page():
    """AI Diagnostics page route"""
    
    apply_shopfloor_theme()
    
    # Create layout shell
    content = layout_shell(
        title="AI Diagnostics",
        show_drawer=True
    )
    
    # Render page content
    with content:
        create_page_header(
            title="AI Diagnostics",
            subtitle="Sprint 3: AI-grounded, explainable diagnostics based on semantic signals and RAG knowledge",
            icon="psychology_alt"
        )
        
        # Render the existing Diagnostics screen
        render_diagnostics_screen()
