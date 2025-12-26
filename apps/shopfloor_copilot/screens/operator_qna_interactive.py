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
        """Refreshable chat message container with improved styling"""
        with ui.column().classes('w-full gap-4'):
            for msg in app.storage.user['messages']:
                if msg['role'] == 'user':
                    with ui.row().classes('w-full justify-end'):
                        with ui.card().classes('bg-blue-600 text-white max-w-2xl p-4 rounded-2xl shadow-lg'):
                            ui.label(msg['content']).classes('text-base font-medium')
                
                elif msg['role'] == 'assistant':
                    with ui.row().classes('w-full justify-start'):
                        with ui.column().classes('max-w-3xl gap-3'):
                            with ui.card().classes('bg-gray-800 border-2 border-gray-600 p-5 rounded-2xl shadow-md'):
                                ui.markdown(msg['content']).classes('text-base text-gray-200 leading-relaxed')
                                if msg.get('model'):
                                    ui.label(f"🤖 {msg['model']}").classes('text-xs text-gray-600 mt-3 font-mono')
                            
                            # Citations with better styling
                            if msg.get('citations'):
                                ui.label('📚 Sources:').classes('text-sm font-bold text-gray-900 mt-2')
                                with ui.row().classes('gap-3 flex-wrap'):
                                    for cit in msg['citations'][:4]:
                                        with ui.card().classes('p-3 bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-300 rounded-lg'):
                                            ui.label(f"📄 {cit['doc_id']}").classes('text-sm font-bold text-gray-900')
                                            if cit.get('pages'):
                                                ui.label(f"Pages: {cit['pages']}").classes('text-xs text-gray-700')
                                            if cit.get('score'):
                                                ui.label(f"Relevance: {cit['score']:.1%}").classes('text-xs text-blue-600 font-semibold')
                
                elif msg['role'] == 'error':
                    with ui.row().classes('w-full justify-center'):
                        with ui.card().classes('bg-red-50 border-2 border-red-300 p-4 rounded-lg'):
                            ui.label(msg['content']).classes('text-base text-red-800 font-medium')
    
    # Main layout
    with ui.row().classes('w-full gap-6 h-full p-4'):
        # Left sidebar - Filters with better styling
        with ui.column().classes('w-80 gap-4'):
            with ui.card().classes('p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200'):
                ui.label('🔧 MES Context Filters').classes('text-xl font-bold text-gray-900 mb-4')
                
                ui.select(
                    ['P01', 'P02'], 
                    label='Plant',
                    on_change=lambda e: update_filter('plant', e.value)
                ).classes('w-full').props('outlined dense bg-color=white').style('background: white; color: #111827;')
                
                ui.select(
                    ['M10', 'B02', 'C03', 'D01', 'SMT1', 'WC01'], 
                    label='Line',
                    on_change=lambda e: update_filter('line', e.value)
                ).classes('w-full mt-3').props('outlined dense bg-color=white').style('background: white; color: #111827;')
                
                ui.select(
                    ['S110', 'S120', 'S130', 'S140'], 
                    label='Station',
                    on_change=lambda e: update_filter('station', e.value)
                ).classes('w-full mt-3').props('outlined dense bg-color=white').style('background: white; color: #111827;')
                
                ui.select(
                    ['T1', 'T2', 'T3'], 
                    label='Shift (Turno)',
                    on_change=lambda e: update_filter('turno', e.value)
                ).classes('w-full mt-3').props('outlined dense bg-color=white').style('background: white; color: #111827;')
                
                ui.button('Clear All Filters', icon='clear', on_click=lambda: [
                    update_filter(k, None) for k in app.storage.user['filters'].keys()
                ]).classes('w-full mt-4 bg-gray-700 text-white hover:bg-gray-800').props('no-caps')
            
            # Suggested questions with better styling
            with ui.card().classes('p-6 bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200'):
                ui.label('💡 Quick Questions').classes('text-lg font-bold text-gray-900 mb-4')
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
                    ).classes('w-full mb-2 text-left bg-white hover:bg-green-100 text-gray-900 justify-start').props('no-caps flat')
        
        # Right - Chat interface with improved design
        with ui.column().classes('flex-grow gap-4 h-full'):
            # Header with better styling
            with ui.card().classes('p-4 bg-gradient-to-r from-blue-600 to-indigo-600'):
                with ui.row().classes('w-full justify-between items-center'):
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('smart_toy', size='lg').classes('text-white')
                        ui.label('💬 AI Operator Assistant').classes('text-2xl font-bold text-white')
                    ui.button('Clear Chat', icon='delete', on_click=clear_chat).classes('bg-white text-blue-600 hover:bg-gray-100').props('no-caps')
            
            # Chat messages with better scroll area styling
            with ui.scroll_area().classes('flex-grow border-2 border-gray-600 rounded-xl p-6 bg-gray-900'):
                chat_container()
            
            # Input area with modern styling
            with ui.card().classes('p-4 bg-gray-800 border-2 border-blue-500'):
                ui_elements['query_input'] = ui.textarea(
                    placeholder='📝 Ask me about work instructions, procedures, safety, troubleshooting...'
                ).classes('w-full text-gray-900').props('outlined rows=3 bg-color=white').style('background: white; color: #111827;')
                
                # Handle enter key (Ctrl+Enter to send, Enter for new line)
                ui_elements['query_input'].on('keydown.ctrl.enter', handle_send)
                
                with ui.row().classes('w-full justify-between items-center mt-3'):
                    ui.label('⌨️ Ctrl+Enter to send').classes('text-sm text-gray-600')
                    ui.button(
                        'Send Message', 
                        icon='send',
                        on_click=handle_send
                    ).classes('bg-blue-600 text-white hover:bg-blue-700 px-6 py-2 text-base').props('no-caps')
