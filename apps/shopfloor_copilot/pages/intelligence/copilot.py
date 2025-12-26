from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.advanced_rag import advanced_rag_screen

@ui.page('/intelligence/copilot')
def ai_copilot_page():
    with layout_shell(title="AI Copilot", theme="dark"):
        create_page_header(
            "AI Copilot",
            "Advanced RAG-powered Q&A assistant",
            "psychology",
            theme="dark"
        )
        advanced_rag_screen()
