import os
import httpx
from nicegui import ui, app
from typing import Optional

def build_operator_qna():
    """Interactive Operator Q&A screen with Ollama LLM integration"""
    
    # Session state
    if 'messages' not in app.storage.user:
        app.storage.user['messages'] = []
    if 'filters' not in app.storage.user:
        app.storage.user['filters'] = {
            'plant': None,
            'line': None,
            'station': None,
            'turno': None
        }
    
    # Store UI elements
    ui_elements = {}
    
    async def handle_send():
        """Handle send button click"""
        if 'query_input' in ui_elements:
            await send_query(ui_elements['query_input'].value)
    
    async def send_query(query_text: str):
        """Send query to backend and display results"""
        if not query_text or not query_text.strip():
            return
        
        # Add user message
        app.storage.user['messages'].append({
            'role': 'user',
            'content': query_text
        })
        if 'query_input' in ui_elements:
            ui_elements['query_input'].value = ''
        chat_container.refresh()
        
        # Add loading indicator with details
        app.storage.user['messages'].append({
            'role': 'assistant',
            'content': '🔍 Searching documents...\n⏳ Generating answer with AI...\n\n_(This may take 1-2 minutes on CPU)_',
            'loading': True
        })
        chat_container.refresh()
        
        # Call API
        try:
            api_base = os.getenv("API_BASE", "http://localhost:8010/api")
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
                response = await client.post(
                    f"{api_base}/ask/llm",
                    json={
                        "app": "shopfloor",
                        "query": query_text,
                        "filters": app.storage.user['filters'],
                        "role": "operator",
                        "use_llm": True
                    }
                )
                result = response.json()
                
                # Remove loading indicator
                app.storage.user['messages'] = [
                    m for m in app.storage.user['messages'] 
                    if not m.get('loading')
                ]
                
                # Add assistant response
                app.storage.user['messages'].append({
                    'role': 'assistant',
                    'content': result.get('answer', ''),
                    'citations': result.get('citations', []),
                    'model': result.get('model', '')
                })
        except Exception as e:
            # Remove loading indicator
            app.storage.user['messages'] = [
                m for m in app.storage.user['messages'] 
                if not m.get('loading')
            ]
            app.storage.user['messages'].append({
                'role': 'error',
                'content': f'Error: {str(e)}'
            })
        
        chat_container.refresh()
    
    def clear_chat():
        """Clear chat history"""
        app.storage.user['messages'] = []
        chat_container.refresh()
    
    def update_filter(key: str, value: Optional[str]):
        """Update MES context filter"""
        app.storage.user['filters'][key] = value if value else None
    
    async def use_suggestion(suggestion: str):
        """Use a suggested question"""
        await send_query(suggestion)
    
    @ui.refreshable
    def chat_container():
        """Refreshable chat message container"""
        with ui.column().classes('w-full gap-3'):
            for msg in app.storage.user['messages']:
                if msg['role'] == 'user':
                    with ui.row().classes('w-full justify-end'):
                        with ui.card().classes('sf-card bg-teal-100 dark:bg-teal-900 max-w-2xl'):
                            ui.label(msg['content']).classes('text-sm')
                
                elif msg['role'] == 'assistant':
                    with ui.row().classes('w-full justify-start'):
                        with ui.column().classes('max-w-3xl gap-2'):
                            with ui.card().classes('sf-card'):
                                ui.markdown(msg['content']).classes('text-sm')
                                if msg.get('model'):
                                    ui.label(f"🤖 {msg['model']}").classes('text-xs opacity-50 mt-2')
                            
                            # Citations
                            if msg.get('citations'):
                                ui.label('Sources:').classes('text-xs font-bold opacity-70 mt-1')
                                with ui.row().classes('gap-2 flex-wrap'):
                                    for cit in msg['citations'][:4]:
                                        with ui.card().classes('sf-card p-2 bg-gray-50 dark:bg-gray-800'):
                                            ui.label(f"📄 {cit['doc_id']}").classes('text-xs font-bold')
                                            ui.label(f"Pages: {cit['pages']}").classes('text-xs opacity-70')
                                            if cit.get('score'):
                                                ui.label(f"Score: {cit['score']:.3f}").classes('text-xs opacity-50')
                
                elif msg['role'] == 'error':
                    with ui.row().classes('w-full justify-center'):
                        with ui.card().classes('sf-card bg-red-100 dark:bg-red-900'):
                            ui.label(msg['content']).classes('text-sm text-red-800 dark:text-red-200')
    
    # Main layout
    with ui.row().classes('w-full gap-4 h-full'):
        # Left sidebar - Filters
        with ui.column().classes('w-72 gap-2'):
            with ui.card().classes('sf-card'):
                ui.label('🔧 MES Context').classes('text-lg font-bold mb-4')
                
                ui.select(
                    ['P01', 'P02'], 
                    label='Plant',
                    on_change=lambda e: update_filter('plant', e.value)
                ).classes('w-full')
                
                ui.select(
                    ['M10', 'B02', 'C03', 'D01', 'SMT1', 'WC01'], 
                    label='Line',
                    on_change=lambda e: update_filter('line', e.value)
                ).classes('w-full')
                
                ui.select(
                    ['S110', 'S120', 'S130', 'S140'], 
                    label='Station',
                    on_change=lambda e: update_filter('station', e.value)
                ).classes('w-full')
                
                ui.select(
                    ['T1', 'T2', 'T3'], 
                    label='Shift (Turno)',
                    on_change=lambda e: update_filter('turno', e.value)
                ).classes('w-full')
                
                ui.button('Clear Filters', icon='clear', on_click=lambda: [
                    update_filter(k, None) for k in app.storage.user['filters'].keys()
                ]).classes('sf-btn secondary w-full mt-2')
            
            # Suggested questions
            with ui.card().classes('sf-card'):
                ui.label('💡 Suggestions').classes('text-sm font-bold mb-3')
                suggestions = [
                    'Show me OEE trend for Line M10',
                    'What are the safety procedures?',
                    'How to handle quality issues?',
                    'Emergency stop procedure'
                ]
                for suggestion in suggestions:
                    ui.button(
                        suggestion, 
                        icon='arrow_forward',
                        on_click=lambda s=suggestion: use_suggestion(s)
                    ).classes('sf-btn ghost justify-between w-full mb-2 text-left').props('flat')
        
        # Right - Chat interface
        with ui.column().classes('flex-grow gap-2 h-full'):
            # Header
            with ui.card().classes('sf-card'):
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label('💬 Operator Assistant').classes('text-lg font-bold')
                    ui.button('Clear Chat', icon='delete', on_click=clear_chat).classes('sf-btn secondary')
            
            # Chat messages (scrollable)
            with ui.scroll_area().classes('flex-grow border border-gray-200 dark:border-gray-700 rounded-lg p-4'):
                chat_container()
            
            # Input area
            with ui.card().classes('sf-card'):
                ui_elements['query_input'] = ui.textarea(
                    placeholder='Ask a question about work instructions, procedures, safety...'
                ).classes('w-full').props('autogrow outlined rows=2')
                
                # Handle enter key (Ctrl+Enter to send, Enter for new line)
                ui_elements['query_input'].on('keydown.ctrl.enter', handle_send)
                
                with ui.row().classes('w-full justify-end gap-2 mt-2'):
                    ui.label('Ctrl+Enter to send').classes('text-xs opacity-50')
                    ui.button(
                        'Send', 
                        icon='send',
                        on_click=handle_send
                    ).classes('sf-btn')
