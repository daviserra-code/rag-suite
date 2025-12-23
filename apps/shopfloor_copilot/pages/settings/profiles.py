"""
Domain Profile Management UI
Sprint 4 — Material Intelligence & Domain Profiles

Allows runtime switching between domain profiles without code changes.
"""

from nicegui import ui
from apps.shopfloor_copilot.theme import apply_shopfloor_theme
from apps.shopfloor_copilot.ui_shell import layout_shell
from apps.shopfloor_copilot.domain_profiles import (
    profile_manager,
    get_active_profile,
    switch_profile,
    list_profiles
)


@ui.page('/settings/profiles')
def profile_management_page():
    """
    Domain profile management page.
    
    Features:
    - View all available profiles
    - See active profile details
    - Switch profiles at runtime
    - View profile configuration
    """
    apply_shopfloor_theme()
    
    with layout_shell(title="Domain Profile Settings", theme="dark"):
        ui.label('Domain Profile Management').classes('text-3xl font-bold text-white mb-2')
        ui.label('Sprint 4 — Material Intelligence & Domain Profiles').classes('text-gray-400 mb-6')
        
        # Info banner
        with ui.card().classes('w-full bg-blue-900 border-blue-700 mb-6'):
            with ui.row().classes('items-center gap-4'):
                ui.icon('info', size='lg').classes('text-blue-300')
                with ui.column().classes('gap-1'):
                    ui.label('Single Codebase, Configuration-Driven Behavior').classes('font-semibold text-blue-100')
                    ui.label('Switch between Aerospace & Defence, Pharma, and Automotive profiles without code changes').classes('text-sm text-blue-200')
        
        # Container for dynamic content
        profile_container = ui.column().classes('w-full gap-6')
        
        def render_profiles():
            """Render the profile selection interface"""
            profile_container.clear()
            
            with profile_container:
                # Get profiles
                profiles = list_profiles()
                active = get_active_profile()
                
                # Active profile card
                with ui.card().classes('w-full bg-gradient-to-r from-green-900 to-green-800 border-green-600'):
                    ui.label('🎯 Active Profile').classes('text-2xl font-bold text-white mb-4')
                    
                    with ui.row().classes('w-full items-start gap-6'):
                        # Profile icon
                        with ui.card().classes('bg-green-700 border-green-500 p-6'):
                            if active.name == 'aerospace_defence':
                                ui.icon('flight', size='3rem').classes('text-white')
                            elif active.name == 'pharma_process':
                                ui.icon('biotech', size='3rem').classes('text-white')
                            else:
                                ui.icon('precision_manufacturing', size='3rem').classes('text-white')
                        
                        # Profile details
                        with ui.column().classes('flex-grow gap-2'):
                            ui.label(active.display_name).classes('text-2xl font-bold text-white')
                            ui.label(active.description).classes('text-gray-300')
                            
                            with ui.row().classes('gap-4 mt-4'):
                                ui.badge(f'Material: {active.material_model.identification}', color='blue').classes('text-sm')
                                ui.badge(f'Traceability: {active.material_model.traceability_level}', color='purple').classes('text-sm')
                                ui.badge(f'Tone: {active.diagnostics_behavior.tone}', color='teal').classes('text-sm')
                                ui.badge(f'Emphasis: {active.diagnostics_behavior.emphasis}', color='orange').classes('text-sm')
                
                # Available profiles
                ui.label('Available Profiles').classes('text-2xl font-bold text-white mt-8 mb-4')
                
                with ui.row().classes('w-full gap-4 flex-wrap'):
                    for profile_info in profiles:
                        is_active = profile_info['active']
                        profile_name = profile_info['name']
                        
                        # Profile card
                        card_class = 'border-green-500 bg-green-950' if is_active else 'border-slate-600 bg-slate-800 hover:bg-slate-750'
                        
                        with ui.card().classes(f'w-80 {card_class} cursor-pointer transition-all').on('click', lambda pn=profile_name: switch_and_refresh(pn) if not is_active else None):
                            # Header
                            with ui.row().classes('w-full items-center justify-between mb-3'):
                                with ui.row().classes('items-center gap-2'):
                                    if profile_name == 'aerospace_defence':
                                        ui.icon('flight', size='lg').classes('text-blue-400')
                                    elif profile_name == 'pharma_process':
                                        ui.icon('biotech', size='lg').classes('text-green-400')
                                    else:
                                        ui.icon('precision_manufacturing', size='lg').classes('text-orange-400')
                                    
                                    ui.label(profile_info['display_name']).classes('text-lg font-semibold text-white')
                                
                                if is_active:
                                    ui.badge('ACTIVE', color='green')
                            
                            # Description
                            ui.label(profile_info['description']).classes('text-sm text-gray-400 mb-4')
                            
                            # Switch button (if not active)
                            if not is_active:
                                with ui.row().classes('w-full justify-end'):
                                    ui.button('Switch to this profile', icon='swap_horiz').props('flat color=primary size=sm')
                
                # Profile details expansion
                ui.label('Profile Configuration Details').classes('text-2xl font-bold text-white mt-8 mb-4')
                
                with ui.expansion('Material Model', icon='inventory_2').classes('w-full bg-slate-800 text-white'):
                    with ui.column().classes('p-4 gap-2'):
                        ui.label(f"Identification: {active.material_model.identification}").classes('text-gray-300')
                        ui.label(f"Genealogy Depth: {active.material_model.genealogy_depth}").classes('text-gray-300')
                        ui.label(f"Revision Required: {'Yes' if active.material_model.revision_required else 'No'}").classes('text-gray-300')
                        ui.label(f"Expiry Management: {active.material_model.expiry_management}").classes('text-gray-300')
                        ui.label(f"Traceability Level: {active.material_model.traceability_level}").classes('text-gray-300')
                        ui.label("Mandatory Fields:").classes('text-gray-300 mt-2 font-semibold')
                        for field in active.material_model.material_mandatory_fields:
                            ui.label(f"  • {field}").classes('text-gray-400 ml-4')
                
                with ui.expansion('Equipment Model', icon='settings').classes('w-full bg-slate-800 text-white'):
                    with ui.column().classes('p-4 gap-2'):
                        ui.label(f"Certification Required: {'Yes' if active.equipment_model.certification_required else 'No'}").classes('text-gray-300')
                        ui.label(f"Calibration Required: {'Yes' if active.equipment_model.tooling_calibration_required else 'No'}").classes('text-gray-300')
                        ui.label(f"Maintenance Log Mandatory: {'Yes' if active.equipment_model.maintenance_log_mandatory else 'No'}").classes('text-gray-300')
                        ui.label(f"Qualification Tracking: {'Yes' if active.equipment_model.qualification_tracking else 'No'}").classes('text-gray-300')
                
                with ui.expansion('Process Constraints', icon='policy').classes('w-full bg-slate-800 text-white'):
                    with ui.column().classes('p-4 gap-2'):
                        ui.label(f"Deviation Required: {'Yes' if active.process_constraints.deviation_required_for_exceptions else 'No'}").classes('text-gray-300')
                        ui.label(f"Operator Certification Required: {'Yes' if active.process_constraints.operator_certification_required else 'No'}").classes('text-gray-300')
                        ui.label(f"Documentation Signoff Required: {'Yes' if active.process_constraints.documentation_signoff_required else 'No'}").classes('text-gray-300')
                        ui.label(f"Work Instruction Mandatory: {'Yes' if active.process_constraints.work_instruction_mandatory else 'No'}").classes('text-gray-300')
                        ui.label(f"Quality Gate Enforcement: {active.process_constraints.quality_gate_enforcement}").classes('text-gray-300')
                
                with ui.expansion('Reason Taxonomy', icon='category').classes('w-full bg-slate-800 text-white'):
                    with ui.column().classes('p-4 gap-2'):
                        ui.label("Enabled Categories (Level 1):").classes('text-gray-300 font-semibold mb-2')
                        for cat in active.reason_taxonomy.enabled:
                            ui.label(f"  • {cat}").classes('text-gray-400 ml-4')
                        
                        ui.label("Subcategories (Level 2):").classes('text-gray-300 font-semibold mt-4 mb-2')
                        for cat, subcats in active.reason_taxonomy.subcategories.items():
                            ui.label(f"{cat}:").classes('text-gray-300 ml-4 font-semibold')
                            for subcat in subcats:
                                ui.label(f"  • {subcat}").classes('text-gray-400 ml-8')
                
                with ui.expansion('RAG Preferences', icon='search').classes('w-full bg-slate-800 text-white'):
                    with ui.column().classes('p-4 gap-2'):
                        ui.label("Priority Sources:").classes('text-gray-300 font-semibold mb-2')
                        for source in active.rag_preferences.priority_sources:
                            weight = active.rag_preferences.search_weights.get(source, 1.0)
                            ui.label(f"  • {source} (weight: {weight}x)").classes('text-gray-400 ml-4')
                
                with ui.expansion('Diagnostics Behavior', icon='psychology').classes('w-full bg-slate-800 text-white'):
                    with ui.column().classes('p-4 gap-2'):
                        ui.label(f"Tone: {active.diagnostics_behavior.tone}").classes('text-gray-300')
                        ui.label(f"Emphasis: {active.diagnostics_behavior.emphasis}").classes('text-gray-300')
                        ui.label(f"Include Documentation Refs: {'Yes' if active.diagnostics_behavior.include_documentation_refs else 'No'}").classes('text-gray-300')
                        ui.label(f"Reasoning Style: {active.diagnostics_behavior.reasoning_style}").classes('text-gray-300')
                        ui.label(f"Output Template: {active.diagnostics_behavior.output_template}").classes('text-gray-300')
        
        def switch_and_refresh(profile_name: str):
            """Switch profile and refresh UI"""
            success = switch_profile(profile_name)
            if success:
                ui.notify(f'✅ Switched to {profile_name}', type='positive')
                render_profiles()
            else:
                ui.notify(f'❌ Failed to switch to {profile_name}', type='negative')
        
        # Initial render
        render_profiles()
