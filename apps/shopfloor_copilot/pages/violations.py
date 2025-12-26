"""
Violations Management Page
"""

from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell
from apps.shopfloor_copilot.screens.violations_management import render_violations_management


@ui.page('/quality/violations')
def violations_page():
    """Violations management page - dark themed"""
    
    # Create shell layout with dark theme
    content = layout_shell(title='Violations Management', show_drawer=True, theme='dark')
    
    # Render violations content
    with content:
        render_violations_management()
