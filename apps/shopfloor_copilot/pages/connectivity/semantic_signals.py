"""
Semantic Signals Page - Sprint 2: Kepware-like mapping
"""

from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.semantic_signals import render_semantic_signals as render_semantic_signals_screen
from apps.shopfloor_copilot.theme import apply_shopfloor_theme


@ui.page('/connectivity/mapping')
def semantic_signals_page():
    """Semantic Signals / Mapping page route"""
    
    apply_shopfloor_theme()
    
    # Create layout shell
    content = layout_shell(
        title="Semantic Signals",
        show_drawer=True,
        theme="legacy"
    )
    
    # Render page content
    with content:
        create_page_header(
            title="Semantic Signals",
            subtitle="Sprint 2: Kepware-like semantic mapping with loss category classification",
            icon="transform",
            theme="legacy"
        )
        
        # Render the existing Semantic Signals screen
        render_semantic_signals_screen()
