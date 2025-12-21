from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.digital_twin import digital_twin_screen

@ui.page('/advanced/twin')
def digital_twin_page():
    with layout_shell(title="Digital Twin"):
        create_page_header(
            "Digital Twin",
            "Manufacturing simulation environment",
            "account_tree"
        )
        digital_twin_screen()
