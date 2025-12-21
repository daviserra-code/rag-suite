from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.energy_tracking import energy_tracking_screen

@ui.page('/analytics/energy')
def energy_tracking_page():
    with layout_shell(title="Energy Tracking"):
        create_page_header(
            "Energy Tracking",
            "Power consumption monitoring and analysis",
            "bolt"
        )
        energy_tracking_screen()
