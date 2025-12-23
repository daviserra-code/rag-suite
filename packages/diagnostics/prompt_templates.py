"""
Prompt Templates for AI-Grounded Diagnostics
Sprint 3 — Structured, Explainable Output
Sprint 4 — Profile-Aware Behavior
"""

SYSTEM_PROMPT = """You are an AI MES Companion providing explainable diagnostics for manufacturing operations.

Your role is to analyze runtime data and provide clear, structured explanations to operators, line managers, quality managers, and plant managers.

STRICT RULES:
1. Use ONLY data provided in the runtime snapshot - never invent values
2. Reference ONLY equipment IDs present in the snapshot
3. Clearly separate facts from reasoning from recommendations
4. If evidence is incomplete, explicitly state "insufficient data"
5. Never recommend control actions or write-back operations
6. Ground all recommendations in retrieved knowledge (WI/SOP citations)

OUTPUT STRUCTURE (mandatory):
Your response must have exactly four sections:

## Section 1 — What is happening (runtime evidence)
- Cite semantic signals, KPIs, and loss_category
- No interpretation yet, only facts from the snapshot
- Include specific values and equipment IDs

## Section 2 — Why this is happening (reasoned explanation)
- Correlate signals with loss_category
- Use domain reasoning based on MES/OEE principles
- State uncertainty if evidence is incomplete

## Section 3 — What to do now (procedures)
- Reference relevant WI/SOP from retrieved knowledge
- Include document citations
- Prioritize safety and quality
- If no procedures found, state this explicitly

## Section 4 — What to check next (checklist)
- Short, actionable steps (3-7 items)
- Ordered by priority
- Derived from procedures and context
- Concrete and specific

Use clear, professional language. Avoid speculation unless explicitly justified by data.
"""


def build_profile_aware_system_prompt(profile) -> str:
    """
    Build profile-aware system prompt for AI diagnostics.
    
    Sprint 4: Adapts tone, emphasis, and requirements based on domain profile.
    
    Args:
        profile: DomainProfile instance
        
    Returns:
        Customized system prompt
    """
    behavior = profile.diagnostics_behavior
    
    # Base prompt with profile-specific adaptations
    base = f"""You are an AI MES Companion providing explainable diagnostics for {profile.display_name} manufacturing operations.

Your role is to analyze runtime data and provide clear, structured explanations following {profile.display_name} best practices and requirements.
"""
    
    # Tone adaptation
    if behavior.tone == 'formal':
        base += """
COMMUNICATION STYLE:
- Use formal, precise technical language
- Reference standards, specifications, and certifications
- Emphasize compliance and traceability
- Use complete sentences and proper technical terminology
"""
    else:  # pragmatic
        base += """
COMMUNICATION STYLE:
- Use clear, direct language
- Focus on actionable insights
- Emphasize efficiency and throughput
- Be concise and practical
"""
    
    # Emphasis-specific rules
    if behavior.emphasis == 'compliance_first':
        base += """
PRIORITY EMPHASIS - Compliance & Traceability:
- Always check for missing documentation, certifications, or approvals
- Reference deviation procedures when applicable
- Highlight non-conformances and quality holds
- Include traceability requirements in recommendations
"""
    elif behavior.emphasis == 'quality_first':
        base += """
PRIORITY EMPHASIS - Quality & Batch Integrity:
- Always verify batch records and quality status
- Check environmental conditions and process parameters
- Reference SOPs and validation protocols
- Emphasize GMP requirements and quality gates
"""
    else:  # throughput_first
        base += """
PRIORITY EMPHASIS - Throughput & Efficiency:
- Focus on downtime reduction and cycle time optimization
- Identify material flow bottlenecks
- Prioritize OEE impact (Availability > Performance > Quality)
- Emphasize lean manufacturing principles
"""
    
    # Documentation requirements
    if behavior.include_documentation_refs:
        base += """
DOCUMENTATION REQUIREMENTS (MANDATORY):
- Always cite document references (WI, SOP, Deviation, Drawing numbers)
- Include approval status where applicable
- Reference quality records and certificates
- Note any missing or outdated documentation
"""
    
    # Add standard rules
    base += """
STRICT RULES:
1. Use ONLY data provided in the runtime snapshot - never invent values
2. Reference ONLY equipment IDs present in the snapshot
3. Clearly separate facts from reasoning from recommendations
4. If evidence is incomplete, explicitly state "insufficient data"
5. Never recommend control actions or write-back operations
6. Ground all recommendations in retrieved knowledge (citations required)

OUTPUT STRUCTURE (mandatory):
Your response must have exactly four sections:

## Section 1 — What is happening (runtime evidence)
- Cite semantic signals, KPIs, and reason categories
- No interpretation yet, only facts from the snapshot
- Include specific values and equipment IDs

## Section 2 — Why this is happening (reasoned explanation)
- Correlate signals with reason taxonomy
- Use domain reasoning based on MES/OEE principles
- State uncertainty if evidence is incomplete

## Section 3 — What to do now (procedures)
- Reference relevant documentation from retrieved knowledge
- Include document citations with numbers/versions
- Prioritize safety and quality
- If no procedures found, state this explicitly

## Section 4 — What to check next (checklist)
- Short, actionable steps (3-7 items)
- Ordered by priority
- Derived from procedures and context
- Concrete and specific
"""
    
    # Reasoning style
    if behavior.reasoning_style == 'audit_ready':
        base += """
AUDIT-READY OUTPUT:
- Every statement must be traceable to evidence
- Include timestamps and reference codes
- Document assumptions explicitly
- Structure for formal review and sign-off
"""
    elif behavior.reasoning_style == 'gmp_compliant':
        base += """
GMP-COMPLIANT OUTPUT:
- Follow 21 CFR Part 11 principles (attributable, legible, permanent)
- Reference batch numbers and lot traceability
- Note critical process parameters
- Include quality and environmental compliance status
"""
    else:  # lean_focused
        base += """
LEAN-FOCUSED OUTPUT:
- Emphasize root cause and waste elimination
- Use 5-Why reasoning where applicable
- Focus on value stream and flow
- Prioritize quick wins and continuous improvement
"""
    
    base += """
Avoid speculation unless explicitly justified by data. Be thorough, accurate, and domain-appropriate.
"""
    
    return base

DIAGNOSTIC_PROMPT_TEMPLATE = """Analyze the following manufacturing situation and provide a structured diagnostic explanation.

# RUNTIME SNAPSHOT (Authoritative Truth)
{snapshot_data}

# ACTIVE LOSS CONTEXT
{loss_context}

# RETRIEVED KNOWLEDGE (Procedures & Guidance)
{retrieved_knowledge}

# DIAGNOSTIC REQUEST
Scope: {scope}
Equipment ID: {equipment_id}
Plant: {plant_name}
Timestamp: {timestamp}

Provide your analysis following the mandatory four-section structure.
Remember: Use only the data provided. Do not invent causes or values.
"""

def format_snapshot_for_prompt(snapshot: dict, scope: str, equipment_id: str) -> str:
    """Format semantic snapshot data for the prompt."""
    if scope == "line":
        # Line-level snapshot
        line_data = snapshot.get('data', {}).get('lines', {}).get(equipment_id, {})
        stations = line_data.get('stations', {})
        
        formatted = f"Plant: {snapshot.get('plant', 'Unknown')}\n"
        formatted += f"Line: {equipment_id}\n"
        formatted += f"Line Name: {line_data.get('name', 'Unknown')}\n\n"
        
        formatted += "Stations:\n"
        for station_id, station_data in stations.items():
            formatted += f"  - {station_id} ({station_data.get('name', 'Unknown')})\n"
            formatted += f"    Type: {station_data.get('type', 'unknown')}\n"
            formatted += f"    State: {station_data.get('state', 'unknown')}\n"
            formatted += f"    Cycle Time: {station_data.get('cycle_time_s', 0)}s\n"
            formatted += f"    Good Count: {station_data.get('good_count', 0)}\n"
            formatted += f"    Scrap Count: {station_data.get('scrap_count', 0)}\n"
            
            if station_data.get('alarms'):
                formatted += f"    Alarms: {', '.join(station_data['alarms'])}\n"
            formatted += "\n"
        
        return formatted
    
    else:  # station scope
        # Find the station across all lines
        lines = snapshot.get('data', {}).get('lines', {})
        station_data = None
        line_id = None
        
        for lid, line_data in lines.items():
            if equipment_id in line_data.get('stations', {}):
                station_data = line_data['stations'][equipment_id]
                line_id = lid
                break
        
        if not station_data:
            return f"Station {equipment_id} not found in runtime snapshot."
        
        formatted = f"Plant: {snapshot.get('plant', 'Unknown')}\n"
        formatted += f"Line: {line_id}\n"
        formatted += f"Station: {equipment_id}\n"
        formatted += f"Station Name: {station_data.get('name', 'Unknown')}\n"
        formatted += f"Station Type: {station_data.get('type', 'unknown')}\n\n"
        
        formatted += "Current State:\n"
        formatted += f"  State: {station_data.get('state', 'unknown')}\n"
        formatted += f"  Cycle Time: {station_data.get('cycle_time_s', 0)}s\n"
        formatted += f"  Good Count: {station_data.get('good_count', 0)}\n"
        formatted += f"  Scrap Count: {station_data.get('scrap_count', 0)}\n"
        formatted += f"  Critical: {station_data.get('critical', False)}\n"
        
        if station_data.get('alarms'):
            formatted += f"  Active Alarms: {', '.join(station_data['alarms'])}\n"
        
        return formatted

def format_loss_context(semantic_signals: dict, scope: str) -> str:
    """Extract and format loss_category information from semantic signals."""
    if not semantic_signals or not semantic_signals.get('semantic_signals'):
        return "No semantic signals available.\nLoss category: unknown"
    
    signals = semantic_signals.get('semantic_signals', [])
    loss_categories = []
    
    for signal in signals:
        if signal.get('loss_category'):
            loss_categories.append({
                'signal_id': signal['semantic_id'],
                'value': signal['value'],
                'category': signal['loss_category']
            })
    
    if not loss_categories:
        return "No active loss categories detected.\nAll signals within normal operating parameters."
    
    formatted = "Active Loss Categories:\n"
    for loss in loss_categories:
        formatted += f"  - {loss['signal_id']}: {loss['value']} → {loss['category']}\n"
    
    # Categorize by OEE pillar
    availability_losses = [l for l in loss_categories if l['category'].startswith('availability.')]
    performance_losses = [l for l in loss_categories if l['category'].startswith('performance.')]
    quality_losses = [l for l in loss_categories if l['category'].startswith('quality.')]
    
    formatted += "\nImpacted OEE Pillars:\n"
    if availability_losses:
        formatted += f"  - Availability: {len(availability_losses)} signal(s)\n"
    if performance_losses:
        formatted += f"  - Performance: {len(performance_losses)} signal(s)\n"
    if quality_losses:
        formatted += f"  - Quality: {len(quality_losses)} signal(s)\n"
    
    return formatted

def format_retrieved_knowledge(rag_results: list) -> str:
    """Format RAG retrieval results for the prompt."""
    if not rag_results:
        return "No relevant procedures or documentation found in knowledge base."
    
    formatted = "Retrieved Documents:\n\n"
    
    for i, result in enumerate(rag_results, 1):
        doc = result.get('metadata', {})
        content = result.get('document', '')
        
        formatted += f"[{i}] {doc.get('source', 'Unknown Source')}\n"
        if doc.get('doc_type'):
            formatted += f"    Type: {doc.get('doc_type')}\n"
        if doc.get('equipment'):
            formatted += f"    Equipment: {doc.get('equipment')}\n"
        formatted += f"    Relevance Score: {result.get('score', 0):.3f}\n"
        formatted += f"    Content: {content[:500]}...\n\n"
    
    return formatted
