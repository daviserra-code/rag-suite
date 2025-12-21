from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.plant_overview import build_plant_overview

@ui.page('/operations/plant')
def plant_overview_page():
    with layout_shell(title="Plant Overview"):
        create_page_header(
            "Plant Overview",
            "Multi-line plant-wide performance view",
            "factory"
        )
        build_plant_overview()
