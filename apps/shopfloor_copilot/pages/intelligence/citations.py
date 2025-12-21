from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.answer_citations import build_answer_citations

@ui.page('/intelligence/citations')
def answer_citations_page():
    with layout_shell(title="Answer Citations"):
        create_page_header(
            "Answer Citations",
            "Source verification and document references",
            "book"
        )
        build_answer_citations()
