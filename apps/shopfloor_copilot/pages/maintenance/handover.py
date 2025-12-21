from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.shift_handover import shift_handover_screen

@ui.page('/maintenance/handover')
def shift_handover_page():
    with layout_shell(title="Shift Handover"):
        create_page_header(
            "Shift Handover",
            "Shift transition notes and communication",
            "sync_alt"
        )
        shift_handover_screen()
