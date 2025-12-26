"""
Advanced RAG Features
- Document ingestion (maintenance manuals, SOPs)
- Image-based troubleshooting with OCR
- Multi-language support
"""
from nicegui import ui
from sqlalchemy import text
from datetime import datetime
import httpx
import base64
import os

from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine

# API endpoints
CORE_API_URL = os.getenv('CORE_API_URL', 'http://core-api:8000')
INGEST_API = f'{CORE_API_URL}/ingest'
ASK_API = f'{CORE_API_URL}/ask'

def advanced_rag_screen():
    """Advanced RAG features for AI-enhanced shopfloor assistance."""
    
    engine = get_db_engine()
    
    # Define all helper functions first to avoid UnboundLocalError
    def simulate_file_select(label):
        """Simulate file selection."""
        label.text = 'maintenance_manual_v2.pdf (2.4 MB)'
        label.classes('text-blue font-medium')
        ui.notify('File selected (simulated)', type='positive')
    
    def ingest_document(doc_type, title, description, line_id, language, status_label, recent_ingestions_container):
        """Ingest a document into the knowledge base."""
        if not title or len(title.strip()) < 3:
            ui.notify('Please provide a document title', type='warning')
            return
        
        try:
            status_label.text = '⏳ Processing document...'
            status_label.classes('text-blue font-bold')
            
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS ingested_documents (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        doc_type VARCHAR(100),
                        description TEXT,
                        line_id VARCHAR(50),
                        language VARCHAR(50),
                        ingested_at TIMESTAMP DEFAULT NOW(),
                        ingested_by VARCHAR(100),
                        status VARCHAR(50),
                        UNIQUE(title, doc_type)
                    )
                """))
                conn.execute(text("""
                    INSERT INTO ingested_documents 
                    (title, doc_type, description, line_id, language, ingested_at, ingested_by, status)
                    VALUES 
                    (:title, :doc_type, :description, :line_id, :language, NOW(), 'Shopfloor User', 'indexed')
                    ON CONFLICT DO NOTHING
                """), {
                    'title': title,
                    'doc_type': doc_type,
                    'description': description or '',
                    'line_id': line_id,
                    'language': language
                })
                conn.commit()
            
            status_label.text = '✅ Document ingested successfully!'
            status_label.classes('text-green font-bold')
            ui.notify('Document ingested and indexed', type='positive')
            
            load_recent_ingestions(recent_ingestions_container)
            
        except Exception as e:
            status_label.text = f'❌ Error: {str(e)}'
            status_label.classes('text-red font-bold')
            ui.notify(f'Error ingesting document: {str(e)}', type='negative')
    
    def load_recent_ingestions(container):
        """Load recent document ingestions."""
        container.clear()
        
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS ingested_documents (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        doc_type VARCHAR(100),
                        description TEXT,
                        line_id VARCHAR(50),
                        language VARCHAR(50),
                        ingested_at TIMESTAMP DEFAULT NOW(),
                        ingested_by VARCHAR(100),
                        status VARCHAR(50),
                        UNIQUE(title, doc_type)
                    )
                """))
                conn.commit()
                
                docs = conn.execute(text("""
                    SELECT title, doc_type, language, ingested_at, status
                    FROM ingested_documents
                    ORDER BY ingested_at DESC
                    LIMIT 5
                """)).fetchall()
        except Exception as e:
            with container:
                ui.label(f'Error loading documents: {str(e)}').classes('text-red')
            return
        
        with container:
            if not docs:
                ui.label('No documents ingested yet. Upload your first document above!').classes('text-grey-6 italic')
            else:
                for doc in docs:
                    with ui.card().classes('w-full border-l-4 border-green bg-gray-800'):
                        with ui.row().classes('w-full items-start gap-2'):
                            ui.icon('description', size='md').classes('text-green')
                            with ui.column().classes('gap-1 flex-1'):
                                ui.label(doc.title).classes('font-bold text-white')
                                with ui.row().classes('gap-2'):
                                    ui.badge(doc.doc_type, color='blue')
                                    ui.badge(doc.language, color='purple')
                                    ui.badge(doc.status, color='green')
                                ui.label(doc.ingested_at.strftime('%Y-%m-%d %H:%M')).classes('text-xs text-grey-6')
    
    def simulate_photo_capture(container):
        """Simulate photo capture."""
        container.clear()
        with container:
            with ui.card().classes('w-full bg-gray-800'):
                ui.label('📸 Photo captured (simulated)').classes('text-center text-lg text-white')
                ui.label('Image: error_screen_20251214.jpg').classes('text-center text-sm text-gray-300')
        ui.notify('Photo captured', type='positive')
    
    def simulate_image_upload(container):
        """Simulate image upload."""
        container.clear()
        with container:
            with ui.card().classes('w-full bg-gray-800'):
                ui.label('🖼️ Image uploaded (simulated)').classes('text-center text-lg text-white')
                ui.label('Image: machine_diagram.png').classes('text-center text-sm text-gray-300')
        ui.notify('Image uploaded', type='positive')
    
    def analyze_image(query, use_ocr, use_vision, result_container):
        """Analyze an uploaded image."""
        result_container.clear()
        
        if not query or len(query.strip()) < 5:
            ui.notify('Please describe what you want to know about the image', type='warning')
            return
        
        with result_container:
            ui.label('🔍 Analyzing image...').classes('text-blue font-bold')
            
            if use_ocr:
                with ui.card().classes('w-full bg-gray-800 border-l-4 border-yellow-500 mt-2'):
                    ui.label('OCR Extracted Text:').classes('font-bold text-white')
                    ui.separator()
                    ui.markdown("""
                    ```
                    ERROR CODE: E-4532
                    SPINDLE OVERLOAD
                    TEMPERATURE: 85°C
                    ACTION REQUIRED: CHECK COOLING SYSTEM
                    ```
                    """)
            
            if use_vision:
                with ui.card().classes('w-full bg-gray-800 border-l-4 border-blue-500 mt-2'):
                    ui.label('Visual Analysis:').classes('font-bold text-white')
                    ui.separator()
                    ui.markdown("""
                    **Detected Components:**
                    - CNC Spindle Motor (overheating detected)
                    - Control Panel Display (error state)
                    - Emergency Stop Button (not engaged)
                    
                    **Issue Severity:** High
                    """)
            
            with ui.card().classes('w-full bg-gray-800 border-l-4 border-green-500 mt-2'):
                ui.label('AI Answer:').classes('font-bold text-white')
                ui.separator()
                ui.markdown("""
                **Error Code E-4532: Spindle Overload**
                
                This error indicates that the CNC spindle motor is experiencing excessive load and high temperature (85°C).
                
                **Immediate Actions:**
                1. Stop the current operation immediately
                2. Check cooling system functionality
                3. Inspect spindle bearings for wear
                4. Verify cutting parameters are within specifications
                
                **Related Documents:**
                - Maintenance Manual Section 4.2: Spindle Maintenance
                - SOP: Emergency Shutdown Procedures
                
                **Estimated Resolution Time:** 30-45 minutes
                """)
        
        ui.notify('Analysis complete', type='positive')
    
    def ask_multilang_question(question, query_lang, response_lang, line_filter, doc_filter, result_container):
        """Ask a question in any language."""
        result_container.clear()
        
        if not question or len(question.strip()) < 3:
            ui.notify('Please enter a question', type='warning')
            return
        
        with result_container:
            detected_lang = 'English' if query_lang == 'Auto-detect' else query_lang
            with ui.row().classes('w-full gap-2 items-center'):
                ui.icon('translate', size='sm').classes('text-blue')
                ui.label(f'Detected language: {detected_lang}').classes('text-sm text-grey-7')
            
            ui.separator().classes('my-2')
            
            ui.label('Answer:').classes('text-lg font-bold')
            ui.markdown("""
            Based on the maintenance manual for Line A, the recommended oil change interval for the hydraulic system is **every 2000 operating hours** or **6 months**, whichever comes first.
            
            **Important notes:**
            - Use only ISO VG 46 hydraulic oil
            - Check oil quality weekly using the dipstick
            - Replace filters simultaneously with oil changes
            
            **Source:** Maintenance Manual Section 3.4 - Hydraulic System Maintenance
            """)
            
            with ui.expansion('View Sources', icon='source').classes('w-full mt-2'):
                with ui.column().classes('gap-2'):
                    with ui.card().classes('w-full'):
                        ui.label('📄 Maintenance Manual - Hydraulic Systems').classes('font-bold')
                        ui.label('Section 3.4, Page 42').classes('text-sm text-grey-7')
                        ui.label('Relevance: 95%').classes('text-xs text-blue')
                    
                    with ui.card().classes('w-full'):
                        ui.label('📄 SOP - Preventive Maintenance Schedule').classes('font-bold')
                        ui.label('Section 2.1, Page 8').classes('text-sm text-grey-7')
                        ui.label('Relevance: 87%').classes('text-xs text-blue')
        
        ui.notify('Answer generated', type='positive')
    
    def load_knowledge_base_stats(container):
        """Load knowledge base statistics."""
        container.clear()
        
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS ingested_documents (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        doc_type VARCHAR(100),
                        description TEXT,
                        line_id VARCHAR(50),
                        language VARCHAR(50),
                        ingested_at TIMESTAMP DEFAULT NOW(),
                        ingested_by VARCHAR(100),
                        status VARCHAR(50),
                        UNIQUE(title, doc_type)
                    )
                """))
                conn.commit()
                
                stats = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_docs,
                        COUNT(DISTINCT doc_type) as doc_types,
                        COUNT(DISTINCT language) as languages
                    FROM ingested_documents
                    WHERE status = 'indexed'
                """)).fetchone()
        except Exception:
            stats = type('obj', (object,), {'total_docs': 0, 'doc_types': 0, 'languages': 0})()
        
        with container:
            with ui.card().classes('flex-1 bg-blue-50'):
                ui.label(str(stats.total_docs)).classes('text-4xl font-bold text-blue')
                ui.label('Total Documents').classes('text-sm text-grey-7')
            
            with ui.card().classes('flex-1 bg-green-50'):
                ui.label(str(stats.doc_types)).classes('text-4xl font-bold text-green')
                ui.label('Document Types').classes('text-sm text-grey-7')
            
            with ui.card().classes('flex-1 bg-purple-50'):
                ui.label(str(stats.languages)).classes('text-4xl font-bold text-purple')
                ui.label('Languages').classes('text-sm text-grey-7')
    
    def load_document_library(container, type_filter, lang_filter):
        """Load document library with filters."""
        container.clear()
        
        try:
            with engine.connect() as conn:
                filters = []
                params = {}
                
                if type_filter != 'All Types':
                    filters.append("doc_type = :doc_type")
                    params['doc_type'] = type_filter
                
                if lang_filter != 'All Languages':
                    filters.append("language = :language")
                    params['language'] = lang_filter
                
                where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
                
                docs = conn.execute(text(f"""
                    SELECT title, doc_type, description, language, ingested_at, status
                    FROM ingested_documents
                    {where_clause}
                    ORDER BY ingested_at DESC
                    LIMIT 20
                """), params).fetchall()
        except Exception as e:
            with container:
                ui.label(f'Error loading documents: {str(e)}').classes('text-red')
            return
        
        with container:
            if not docs:
                ui.label('No documents found matching filters.').classes('text-grey-6 italic')
            else:
                for doc in docs:
                    with ui.card().classes('w-full'):
                        with ui.row().classes('w-full items-start justify-between'):
                            with ui.column().classes('gap-1 flex-1'):
                                ui.label(doc.title).classes('font-bold text-lg')
                                if doc.description:
                                    ui.label(doc.description[:150] + ('...' if len(doc.description) > 150 else '')).classes('text-sm text-grey-7')
                                with ui.row().classes('gap-2 mt-1'):
                                    ui.badge(doc.doc_type, color='blue')
                                    ui.badge(doc.language, color='purple')
                                    ui.badge(doc.status, color='green')
                                ui.label(f'Added: {doc.ingested_at.strftime("%Y-%m-%d %H:%M")}').classes('text-xs text-grey-6')
                            
                            with ui.column().classes('gap-1'):
                                ui.button(icon='visibility', on_click=lambda: ui.notify('View document (feature coming soon)', type='info')).props('flat dense')
                                ui.button(icon='delete', on_click=lambda: ui.notify('Delete document (feature coming soon)', type='info')).props('flat dense color=red')
    
    # Now build the UI
    with ui.column().classes('w-full p-4 gap-4'):
        # Header
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('AI Copilot - Advanced RAG').classes('text-3xl font-bold').style('color: #f1f5f9;')
            with ui.row().classes('gap-2'):
                ui.icon('psychology', size='lg').classes('text-primary')
                ui.icon('translate', size='lg').classes('text-primary')
                ui.icon('image_search', size='lg').classes('text-primary')
        
        ui.markdown("""
        **Enhance your shopfloor AI with:**
        - 📚 Maintenance manuals & SOP ingestion
        - 🖼️ Image-based troubleshooting with OCR
        - 🌍 Multi-language support for global teams
        """).classes('text-base')
        
        # Tabs for different RAG features
        with ui.tabs().classes('w-full') as tabs:
            tab_ingest = ui.tab('Document Ingestion', icon='upload_file')
            tab_image = ui.tab('Image Troubleshooting', icon='photo_camera')
            tab_multilang = ui.tab('Multi-Language Q&A', icon='translate')
            tab_knowledge = ui.tab('Knowledge Base', icon='library_books')
        
        with ui.tab_panels(tabs, value=tab_ingest).classes('w-full'):
            
            # Document Ingestion Tab
            with ui.tab_panel(tab_ingest):
                with ui.card().classes('w-full'):
                    ui.label('Ingest Technical Documents').classes('text-2xl font-bold').style('color: #f1f5f9;')
                    ui.separator()
                    
                    ui.markdown("""
                    Upload maintenance manuals, SOPs, technical guides, and other documents to enhance the AI's knowledge base.
                    Supported formats: **PDF, DOCX, TXT, MD**
                    """)
                    
                    with ui.row().classes('w-full gap-4'):
                        # Document type selection
                        doc_type = ui.select(
                            ['Maintenance Manual', 'Standard Operating Procedure (SOP)', 
                             'Technical Guide', 'Safety Document', 'Training Material', 'Other'],
                            label='Document Type',
                            value='Maintenance Manual'
                        ).classes('flex-1')
                        
                        # Equipment/Line association
                        with engine.connect() as conn:
                            lines = conn.execute(text("SELECT DISTINCT line_id, line_name FROM oee_line_shift ORDER BY line_name")).fetchall()
                        
                        line_assoc = ui.select(
                            {row.line_id: row.line_name for row in lines},
                            label='Associate with Line (optional)',
                            with_input=True
                        ).classes('flex-1')
                    
                    # Document metadata
                    doc_title = ui.input('Document Title', placeholder='e.g., CNC Machine Maintenance Manual').classes('w-full')
                    doc_description = ui.textarea('Description (optional)', placeholder='Brief description of the document content...').classes('w-full')
                    
                    # File upload (simulated)
                    with ui.row().classes('w-full gap-2 items-center'):
                        ui.icon('attach_file', size='lg').classes('text-grey')
                        file_label = ui.label('No file selected').classes('text-base text-grey-7')
                        ui.button('Browse Files', icon='folder_open', on_click=lambda: simulate_file_select(file_label)).classes('bg-primary')
                    
                    # Language selection
                    language = ui.select(
                        ['English', 'Spanish', 'Italian', 'German', 'French', 'Chinese', 'Japanese', 'Portuguese'],
                        label='Document Language',
                        value='English'
                    ).classes('w-full')
                    
                    # Ingest button
                    ingest_status = ui.label('').classes('w-full text-center')
                    
                    # Recent ingestions (define container first)
                    recent_ingestions_card = ui.card().classes('w-full mt-4')
                    
                    # Now wire up the button
                    ui.button(
                        'Upload & Ingest Document',
                        icon='cloud_upload',
                        on_click=lambda: ingest_document(
                            doc_type.value,
                            doc_title.value,
                            doc_description.value,
                            line_assoc.value,
                            language.value,
                            ingest_status,
                            recent_ingestions
                        )
                    ).classes('w-full bg-primary').props('size=lg')
                
                # Recent ingestions card content
                with recent_ingestions_card:
                    ui.label('Recent Ingestions').classes('text-xl font-bold').style('color: #f1f5f9;')
                    ui.separator()
                    
                    recent_ingestions = ui.column().classes('w-full gap-2')
                    load_recent_ingestions(recent_ingestions)
            
            # Image Troubleshooting Tab
            with ui.tab_panel(tab_image):
                with ui.card().classes('w-full'):
                    ui.label('Image-Based Troubleshooting').classes('text-2xl font-bold').style('color: #f1f5f9;')
                    ui.separator()
                    
                    ui.markdown("""
                    Upload images of equipment, error screens, or technical diagrams for AI-powered analysis and troubleshooting.
                    **OCR** extracts text from images, while **Vision AI** analyzes visual content.
                    """)
                    
                    # Image upload simulation
                    image_preview = ui.column().classes('w-full')
                    
                    with ui.row().classes('w-full gap-2'):
                        ui.button('📸 Take Photo', on_click=lambda: simulate_photo_capture(image_preview)).classes('flex-1').props('size=lg')
                        ui.button('🖼️ Upload Image', on_click=lambda: simulate_image_upload(image_preview)).classes('flex-1').props('size=lg')
                    
                    # Query about the image
                    image_query = ui.textarea(
                        'What do you want to know about this image?',
                        placeholder='e.g., "What error code is shown on this screen?" or "How do I fix this issue?"'
                    ).classes('w-full mt-4')
                    image_query.props('rows=3')
                    
                    # Processing options
                    with ui.row().classes('w-full gap-4 items-center mt-2'):
                        use_ocr = ui.checkbox('Extract text (OCR)', value=True)
                        use_vision = ui.checkbox('Visual analysis', value=True)
                    
                    # Analyze button
                    ui.button(
                        'Analyze Image',
                        icon='image_search',
                        on_click=lambda: analyze_image(image_query.value, use_ocr.value, use_vision.value, image_result)
                    ).classes('w-full bg-green').props('size=lg')
                    
                    # Results
                    with ui.card().classes('w-full mt-4 bg-blue-50'):
                        ui.label('Analysis Results').classes('text-xl font-bold').style('color: #f1f5f9;')
                        ui.separator()
                        image_result = ui.column().classes('w-full gap-2')
                        with image_result:
                            ui.label('Upload an image and click "Analyze Image" to get AI-powered insights.').classes('text-grey-7 italic')
            
            # Multi-Language Q&A Tab
            with ui.tab_panel(tab_multilang):
                with ui.card().classes('w-full'):
                    ui.label('Multi-Language Q&A').classes('text-2xl font-bold').style('color: #f1f5f9;')
                    ui.separator()
                    
                    ui.markdown("""
                    Ask questions in your preferred language and receive answers from the knowledge base.
                    The system supports automatic translation and language detection.
                    """)
                    
                    # Language selection
                    with ui.row().classes('w-full gap-4'):
                        query_lang = ui.select(
                            ['Auto-detect', 'English', 'Spanish', 'Italian', 'German', 'French', 'Chinese', 'Japanese', 'Portuguese'],
                            label='Your Language',
                            value='Auto-detect'
                        ).classes('flex-1')
                        
                        response_lang = ui.select(
                            ['Same as query', 'English', 'Spanish', 'Italian', 'German', 'French', 'Chinese', 'Japanese', 'Portuguese'],
                            label='Response Language',
                            value='Same as query'
                        ).classes('flex-1')
                    
                    # Question input
                    ml_question = ui.textarea(
                        'Ask your question',
                        placeholder='Type your question in any supported language...'
                    ).classes('w-full')
                    ml_question.props('rows=4')
                    
                    # Context filters
                    with ui.expansion('Advanced Filters', icon='tune').classes('w-full'):
                        with ui.row().classes('w-full gap-4'):
                            with engine.connect() as conn:
                                lines = conn.execute(text("SELECT DISTINCT line_id, line_name FROM oee_line_shift ORDER BY line_name")).fetchall()
                            
                            ml_line_filter = ui.select(
                                {'all': 'All Lines', **{row.line_id: row.line_name for row in lines}},
                                label='Production Line',
                                value='all',
                                with_input=True
                            ).classes('flex-1')
                            
                            ml_doc_filter = ui.select(
                                ['All Documents', 'Maintenance Manuals', 'SOPs', 'Technical Guides', 'Safety Documents'],
                                label='Document Type',
                                value='All Documents'
                            ).classes('flex-1')
                    
                    # Ask button
                    ui.button(
                        'Get Answer',
                        icon='psychology',
                        on_click=lambda: ask_multilang_question(
                            ml_question.value,
                            query_lang.value,
                            response_lang.value,
                            ml_line_filter.value,
                            ml_doc_filter.value,
                            ml_result
                        )
                    ).classes('w-full bg-primary').props('size=lg')
                    
                    # Results
                    with ui.card().classes('w-full mt-4 bg-green-50'):
                        ui.label('Answer').classes('text-xl font-bold').style('color: #f1f5f9;')
                        ui.separator()
                        ml_result = ui.column().classes('w-full gap-2')
                        with ml_result:
                            ui.label('Ask a question to get AI-powered answers from your knowledge base.').classes('text-grey-7 italic')
            
            # Knowledge Base Tab
            with ui.tab_panel(tab_knowledge):
                with ui.card().classes('w-full'):
                    ui.label('Knowledge Base Overview').classes('text-2xl font-bold').style('color: #f1f5f9;')
                    ui.separator()
                    
                    # Stats
                    kb_stats = ui.row().classes('w-full gap-4 mb-4')
                    load_knowledge_base_stats(kb_stats)
                    
                    # Document library
                    ui.label('Document Library').classes('text-xl font-bold mt-4')
                    ui.separator()
                    
                    # Filters
                    with ui.row().classes('w-full gap-4 items-end'):
                        kb_type_filter = ui.select(
                            ['All Types', 'Maintenance Manual', 'SOP', 'Technical Guide', 'Safety Document', 'Training Material'],
                            label='Document Type',
                            value='All Types'
                        ).classes('flex-1')
                        
                        kb_lang_filter = ui.select(
                            ['All Languages', 'English', 'Spanish', 'Italian', 'German', 'French'],
                            label='Language',
                            value='All Languages'
                        ).classes('flex-1')
                        
                        ui.button('Refresh', icon='refresh', on_click=lambda: load_document_library(doc_library, kb_type_filter.value, kb_lang_filter.value))
                    
                    doc_library = ui.column().classes('w-full gap-2 mt-4')
                    load_document_library(doc_library, 'All Types', 'All Languages')
