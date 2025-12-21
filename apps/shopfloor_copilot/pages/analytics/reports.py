from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.reports import render_reports_screen

@ui.page('/analytics/reports')
def reports_page():
    with layout_shell(title="Reports"):
        create_page_header(
            "Reports",
            "Scheduled reports and exports",
            "description"
        )
        render_reports_screen()
