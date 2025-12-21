from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.live_monitoring import render_live_monitoring_screen

@ui.page('/operations/live')
def live_monitoring_page():
    with layout_shell(title="Live Monitoring"):
        create_page_header(
            "Live Monitoring",
            "Real-time OEE monitoring across all production lines",
            "sensors"
        )
        render_live_monitoring_screen()
