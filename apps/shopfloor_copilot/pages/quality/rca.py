from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.root_cause_analysis import root_cause_analysis_screen

@ui.page('/quality/rca')
def root_cause_analysis_page():
    with layout_shell(title="Root Cause Analysis"):
        create_page_header(
            "Root Cause Analysis",
            "Issue analysis and tracking system",
            "troubleshoot"
        )
        root_cause_analysis_screen()
