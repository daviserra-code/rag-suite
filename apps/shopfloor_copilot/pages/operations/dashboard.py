from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.operations_dashboard import build_operations_dashboard

@ui.page('/operations/dashboard')
def operations_dashboard_page():
    with layout_shell(title="Operations Dashboard"):
        create_page_header(
            "Operations Dashboard",
            "Shift operations control center",
            "dashboard"
        )
        build_operations_dashboard()
