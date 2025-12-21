from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.predictive_maintenance import render_predictive_maintenance_screen

@ui.page('/maintenance/predictive')
def predictive_maintenance_page():
    with layout_shell(title="Predictive Maintenance"):
        create_page_header(
            "Predictive Maintenance",
            "AI-powered failure prediction system",
            "build_circle"
        )
        render_predictive_maintenance_screen()
