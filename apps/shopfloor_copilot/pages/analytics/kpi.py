from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.kpi_dashboard_interactive import build_kpi_dashboard

@ui.page('/analytics/kpi')
def kpi_dashboard_page():
    with layout_shell(title="KPI Dashboard"):
        create_page_header(
            "KPI Dashboard",
            "Key performance indicators and metrics",
            "analytics"
        )
        build_kpi_dashboard()
