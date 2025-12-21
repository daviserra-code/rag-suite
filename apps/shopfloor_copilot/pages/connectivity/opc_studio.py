from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.opc_studio import opc_studio_screen

@ui.page('/connectivity/opc')
def opc_studio_page():
    with layout_shell(title="OPC Studio", theme="legacy"):
        create_page_header(
            "OPC Studio",
            "OPC UA server control panel",
            "settings_input_component",
            theme="legacy"
        )
        opc_studio_screen()
