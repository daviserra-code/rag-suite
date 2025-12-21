from nicegui import ui
from apps.shopfloor_copilot.ui_shell import layout_shell, create_page_header
from apps.shopfloor_copilot.screens.ticket_insights import build_ticket_insights

@ui.page('/advanced/tickets')
def ticket_insights_page():
    with layout_shell(title="Ticket Insights"):
        create_page_header(
            "Ticket Insights",
            "JIRA integration and ticket analytics",
            "confirmation_number"
        )
        build_ticket_insights()
