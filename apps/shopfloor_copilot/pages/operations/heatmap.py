from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.station_heatmap import render_station_heatmap_screen

@ui.page('/operations/heatmap')
def station_heatmap_page():
    with layout_shell(title="Station Heatmap"):
        create_page_header(
            "Station Heatmap",
            "Station performance grid visualization",
            "grid_view"
        )
        render_station_heatmap_screen()
