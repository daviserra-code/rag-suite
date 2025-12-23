"""
Diagnostics Explainer
Sprint 3 — AI-Grounded Diagnostics & Explainability

Core engine for generating explainable diagnostics based on:
- Semantic runtime snapshots
- Loss category taxonomy
- RAG knowledge retrieval
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx

from .prompt_templates import (
    SYSTEM_PROMPT,
    DIAGNOSTIC_PROMPT_TEMPLATE,
    format_snapshot_for_prompt,
    format_loss_context,
    format_retrieved_knowledge
)

# Use existing RAG infrastructure
try:
    from packages.core_rag.chroma_client import get_collection
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("Chroma client not available - RAG retrieval disabled")

logger = logging.getLogger(__name__)

# Service URLs (from environment in production)
import os
OPC_STUDIO_URL = os.getenv("OPC_STUDIO_URL", "http://opc-studio:8040")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
CHROMA_URL = os.getenv("CHROMA_URL", "http://chroma:8000")


class DiagnosticsExplainer:
    """
    AI-powered diagnostics engine that transforms semantic runtime data
    into explainable, actionable insights.
    
    Follows strict guardrails:
    - Uses only authoritative runtime data
    - Never invents values or causes
    - Clearly separates facts from recommendations
    - Grounds all advice in retrieved knowledge
    """
    
    def __init__(
        self,
        opc_url: str = OPC_STUDIO_URL,
        ollama_url: str = OLLAMA_URL,
        chroma_url: str = CHROMA_URL
    ):
        self.opc_url = opc_url
        self.ollama_url = ollama_url
        self.chroma_url = chroma_url
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3.2:3b")  # Default to 3b for efficiency
    
    async def explain_situation(
        self,
        scope: str,
        equipment_id: str,
        profile = None  # DomainProfile context
    ) -> Dict[str, Any]:
        """
        Generate structured, explainable diagnostic for a line or station.
        
        Args:
            scope: "line" or "station"
            equipment_id: Line ID (e.g., "A01") or Station ID (e.g., "ST18")
            profile: Domain profile context (explicit, not global)
        
        Returns:
            Structured diagnostic with 4 sections:
            - what_is_happening: Runtime evidence
            - why_this_is_happening: Reasoned explanation
            - what_to_do_now: Procedures from RAG
            - what_to_check_next: Actionable checklist
        """
        try:
            # Step 0: Load profile context if not provided (explicit, not global)
            if profile is None:
                try:
                    from apps.shopfloor_copilot.domain_profiles import get_active_profile
                    profile = get_active_profile()
                    logger.info(f"Using domain profile: {profile.display_name}")
                except Exception as e:
                    logger.warning(f"Could not load profile: {e}")
                    profile = None
            # Step 1: Fetch semantic snapshot (authoritative truth)
            logger.info(f"Fetching semantic snapshot for {scope} {equipment_id}")
            snapshot = await self._fetch_semantic_snapshot()
            
            if not snapshot:
                return self._error_response("Runtime data unavailable - cannot fetch OPC snapshot")
            
            # Step 2: Extract relevant subset based on scope
            if scope == "station":
                # Get semantic signals for specific station
                semantic_signals = await self._fetch_station_semantic_signals(equipment_id)
            else:  # line scope
                # Get all signals for the line
                semantic_signals = await self._fetch_line_semantic_signals(equipment_id)
            
            # Step 2.5: Evaluate profile expectations (BEFORE LLM)
            # This is deterministic and rule-based
            expectation_result = None
            if profile:
                from packages.diagnostics.expectation_evaluator import evaluate_profile_expectations
                expectation_result = evaluate_profile_expectations(
                    runtime_snapshot=snapshot,
                    semantic_signals=semantic_signals,
                    profile=profile
                )
                logger.info(f"Expectation evaluation: severity={expectation_result.severity}, "
                          f"violations={len(expectation_result.violated_expectations)}, "
                          f"blocking={len(expectation_result.blocking_conditions)}")
            
            # Step 3: Identify active loss_category with profile-aware filtering
            loss_context = self._extract_loss_context(
                semantic_signals,
                scope,
                profile=profile
            )
            
            # Step 4: Query RAG knowledge base with profile context
            logger.info(f"Querying RAG for {scope} {equipment_id}")
            rag_results = await self._query_rag(
                equipment_id=equipment_id,
                loss_categories=[lc['category'] for lc in loss_context.get('active_losses', [])],
                scope=scope,
                profile=profile
            )
            
            # Step 5: Build structured prompt with profile context and expectations
            prompt = self._build_diagnostic_prompt(
                snapshot=snapshot,
                semantic_signals=semantic_signals,
                loss_context=loss_context,
                rag_results=rag_results,
                scope=scope,
                equipment_id=equipment_id,
                profile=profile,
                expectation_result=expectation_result
            )
            
            # Step 6: Call LLM with profile-aware system prompt
            logger.info("Calling LLM for diagnostic generation")
            llm_response = await self._call_llm(prompt, profile=profile)
            
            # Step 7: Parse and structure response
            structured_response = self._parse_llm_response(llm_response)
            
            # Step 8: Add metadata including profile info and expectations
            structured_response['metadata'] = {
                'scope': scope,
                'equipment_id': equipment_id,
                'timestamp': datetime.utcnow().isoformat(),
                'plant': snapshot.get('plant', 'Unknown'),
                'model': self.model_name,
                'loss_categories': [lc['category'] for lc in loss_context.get('active_losses', [])],
                'rag_documents': len(rag_results),
                'domain_profile': profile.display_name if profile else 'None',
                'reasoning_priority': profile.reason_taxonomy.diagnostic_priority_order if profile else [],
                'expectation_violations': expectation_result.violated_expectations if expectation_result else [],
                'blocking_conditions': expectation_result.blocking_conditions if expectation_result else [],
                'requires_confirmation': expectation_result.requires_human_confirmation if expectation_result else False,
                'severity': expectation_result.severity if expectation_result else 'normal'
            }
            
            return structured_response
        
        except Exception as e:
            logger.error(f"Error in explain_situation: {e}", exc_info=True)
            return self._error_response(f"Diagnostic generation failed: {str(e)}")
    
    async def _fetch_semantic_snapshot(self) -> Optional[Dict]:
        """Fetch current OPC snapshot."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.opc_url}/snapshot")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch OPC snapshot: {e}")
            return None
    
    async def _fetch_station_semantic_signals(self, station_id: str) -> Optional[Dict]:
        """Fetch semantic signals for a specific station."""
        try:
            # Find which line contains this station
            snapshot = await self._fetch_semantic_snapshot()
            if not snapshot:
                return None
            
            lines = snapshot.get('data', {}).get('lines', {})
            # Case-insensitive and fuzzy matching for station IDs
            station_id_upper = station_id.upper()
            
            for line_id, line_data in lines.items():
                stations = line_data.get('stations', {})
                # Try exact match first
                if station_id in stations:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(
                            f"{self.opc_url}/semantic/signals/{line_id}/{station_id}"
                        )
                        response.raise_for_status()
                        return response.json()
                
                # Try case-insensitive match
                for sid in stations.keys():
                    if sid.upper() == station_id_upper:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            response = await client.get(
                                f"{self.opc_url}/semantic/signals/{line_id}/{sid}"
                            )
                            response.raise_for_status()
                            return response.json()
            
            # If still not found, try partial match
            for line_id, line_data in lines.items():
                stations = line_data.get('stations', {})
                for sid in stations.keys():
                    if station_id_upper in sid.upper() or sid.upper() in station_id_upper:
                        logger.info(f"Fuzzy matched {station_id} to {sid}")
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            response = await client.get(
                                f"{self.opc_url}/semantic/signals/{line_id}/{sid}"
                            )
                            response.raise_for_status()
                            return response.json()
            
            # List available stations for better error message
            available_stations = []
            for line_data in lines.values():
                available_stations.extend(line_data.get('stations', {}).keys())
            logger.warning(f"Station {station_id} not found. Available stations: {available_stations[:10]}")
            return None
        
        except Exception as e:
            logger.error(f"Failed to fetch station semantic signals: {e}")
            return None
    
    async def _fetch_line_semantic_signals(self, line_id: str) -> Optional[Dict]:
        """Fetch semantic signals for all stations in a line."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.opc_url}/semantic/signals")
                response.raise_for_status()
                all_signals = response.json()
                
                # Filter for the specific line
                line_signals = {
                    'stations': {}
                }
                
                for station_result in all_signals.get('results', []):
                    if station_result.get('line_id') == line_id:
                        station_id = station_result['station_id']
                        line_signals['stations'][station_id] = station_result
                
                return line_signals
        
        except Exception as e:
            logger.error(f"Failed to fetch line semantic signals: {e}")
            return None
    
    def _extract_loss_context(
        self,
        semantic_signals: Optional[Dict],
        scope: str,
        profile = None
    ) -> Dict:
        """
        Extract active loss categories from semantic signals.
        
        Sprint 4: Profile-aware reason filtering
        - Only evaluates reasons in enabled categories
        - Evaluates in profile-specified priority order
        """
        if not semantic_signals:
            return {
                'active_losses': [],
                'availability_affected': False,
                'performance_affected': False,
                'quality_affected': False,
                'reasoning_order': []
            }
        
        # Get enabled categories and priority order from profile
        enabled_categories = None
        priority_order = []
        if profile:
            enabled_categories = set(profile.reason_taxonomy.enabled)
            priority_order = profile.reason_taxonomy.diagnostic_priority_order
            logger.info(f"Profile-aware evaluation order: {priority_order}")
        
        active_losses = []
        
        if scope == "station":
            # Single station
            signals = semantic_signals.get('semantic_signals', [])
            for signal in signals:
                if signal.get('loss_category'):
                    active_losses.append({
                        'signal_id': signal['semantic_id'],
                        'value': signal['value'],
                        'category': signal['loss_category'],
                        'unit': signal.get('unit'),
                        'description': signal.get('description')
                    })
        else:
            # Multiple stations in a line
            for station_id, station_data in semantic_signals.get('stations', {}).items():
                signals = station_data.get('semantic_signals', [])
                for signal in signals:
                    if signal.get('loss_category'):
                        active_losses.append({
                            'station_id': station_id,
                            'signal_id': signal['semantic_id'],
                            'value': signal['value'],
                            'category': signal['loss_category'],
                            'unit': signal.get('unit'),
                            'description': signal.get('description')
                        })
        
        # Categorize by OEE pillar
        availability_affected = any(l['category'].startswith('availability.') for l in active_losses)
        performance_affected = any(l['category'].startswith('performance.') for l in active_losses)
        quality_affected = any(l['category'].startswith('quality.') for l in active_losses)
        
        # Sprint 4: Filter losses by enabled categories
        if enabled_categories:
            filtered_losses = []
            for loss in active_losses:
                # Extract reason category from loss_category (e.g., 'equipment' from 'availability.equipment_failure')
                loss_cat = loss['category'].split('.')[-1]  # e.g., 'equipment_failure'
                # Map to universal category
                for category in ['equipment', 'material', 'process', 'quality', 'documentation', 'people', 'tooling', 'logistics', 'environmental']:
                    if category in loss_cat:
                        if category in enabled_categories:
                            filtered_losses.append(loss)
                        break
            logger.info(f"Filtered {len(active_losses)} losses to {len(filtered_losses)} based on enabled categories")
            active_losses = filtered_losses
        
        # Sprint 4: Sort losses by priority order
        if priority_order and active_losses:
            # Create priority map (lower index = higher priority)
            priority_map = {cat: idx for idx, cat in enumerate(priority_order)}
            
            def get_priority(loss):
                loss_cat = loss['category'].split('.')[-1]
                for category in priority_order:
                    if category in loss_cat:
                        return priority_map.get(category, 999)
                return 999
            
            active_losses.sort(key=get_priority)
            logger.info(f"Sorted losses by priority: {[l['category'] for l in active_losses]}")
        
        return {
            'active_losses': active_losses,
            'availability_affected': availability_affected,
            'performance_affected': performance_affected,
            'quality_affected': quality_affected,
            'reasoning_order': priority_order
        }
    
    async def _query_rag(
        self,
        equipment_id: str,
        loss_categories: List[str],
        scope: str,
        profile = None
    ) -> List[Dict]:
        """
        Query Chroma for relevant procedures and documentation.
        
        Sprint 4: Profile-aware RAG retrieval (EXECUTIVE, not cosmetic)
        - Filters by profile priority_sources BEFORE scoring
        - Applies source-specific weights to ranking
        - Only retrieves documents relevant to active profile
        - Behavioral change: Same query returns different docs per profile
        """
        if not CHROMA_AVAILABLE:
            logger.warning("Chroma client not available")
            return []
        
        try:
            # Sprint 4: Use explicit profile context (not global)
            if profile:
                priority_sources = profile.rag_preferences.priority_sources
                search_weights = profile.rag_preferences.search_weights
                logger.info(f"RAG using profile: {profile.display_name}, priority sources: {priority_sources}")
            else:
                logger.warning("No profile context - using defaults")
                priority_sources = ["work_instructions", "sop", "maintenance_log"]
                search_weights = {}
            
            # Build search query
            query_parts = [equipment_id]
            
            # Add loss category keywords (backward compatible with legacy loss_category)
            for category in loss_categories:
                # Extract specific loss type (e.g., "equipment_failure" from "availability.equipment_failure")
                if '.' in category:
                    loss_type = category.split('.')[-1].replace('_', ' ')
                    query_parts.append(loss_type)
            
            query_text = ' '.join(query_parts)
            
            # Use existing Chroma client infrastructure
            collection = get_collection("shopfloor_docs")
            
            # Sprint 4: Build metadata filter based on profile priority sources
            # Map profile source names to doc_types in Chroma
            source_mapping = {
                'work_instructions': 'work_instruction',
                'work_instruction': 'work_instruction',
                'sops': 'sop',
                'sop': 'sop',
                'deviations': 'deviation',
                'deviation': 'deviation',
                'drawings': 'drawing',
                'drawing': 'drawing',
                'quality_records': 'quality_record',
                'specifications': 'specification',
                'certificates': 'certificate',
                'batch_records': 'batch_record',
                'validation_protocols': 'validation_protocol',
                'coas': 'coa',
                'downtime_patterns': 'downtime_pattern',
                'supplier_performance': 'supplier_data',
                'maintenance_logs': 'maintenance_log',
                'maintenance_log': 'maintenance_log'
            }
            
            # Build metadata filter from priority sources
            doc_types = []
            for source in priority_sources:
                source_lower = source.lower()
                if source_lower in source_mapping:
                    doc_types.append(source_mapping[source_lower])
            
            # Fallback to defaults if no valid mappings
            if not doc_types:
                doc_types = ['work_instruction', 'sop', 'maintenance_log']
            
            # Query with profile-aware metadata filter
            where_clause = {
                "$or": [{"doc_type": dt} for dt in doc_types]
            }
            
            logger.info(f"RAG query: '{query_text}' with doc_types: {doc_types}")
            
            results = collection.query(
                query_texts=[query_text],
                n_results=10,  # Get more results to apply weighting
                where=where_clause
            )
            
            # Format results with profile-aware weighting
            documents = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            distances = results.get('distances', [[]])[0]
            
            weighted_results = []
            for doc, meta, dist in zip(documents, metadatas, distances):
                if dist < 1.5:  # Base similarity threshold
                    # Get doc_type and apply profile weight
                    doc_type = meta.get('doc_type', 'default')
                    
                    # Reverse map to profile source name for weight lookup
                    profile_source = next(
                        (k for k, v in source_mapping.items() if v == doc_type),
                        'default'
                    )
                    
                    # Apply profile weight (higher weight = better ranking)
                    weight = search_weights.get(profile_source, 1.0)
                    weighted_score = (1.0 - dist) * weight
                    
                    weighted_results.append({
                        'document': doc,
                        'metadata': meta,
                        'score': weighted_score,
                        'base_score': 1.0 - dist,
                        'weight': weight,
                        'source_type': profile_source
                    })
            
            # Sort by weighted score (highest first)
            weighted_results.sort(key=lambda x: x['score'], reverse=True)
            
            # Return top 5 after weighting
            return weighted_results[:5]
        
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return []
    
    def _build_diagnostic_prompt(
        self,
        snapshot: Dict,
        semantic_signals: Optional[Dict],
        loss_context: Dict,
        rag_results: List[Dict],
        scope: str,
        equipment_id: str,
        profile = None,
        expectation_result = None
    ) -> str:
        """
        Build the structured diagnostic prompt.
        
        Sprint 4: Profile-aware prompt construction (EXPLICIT context)
        Sprint 4.5: Expectation-aware prompt (LLM explains, not decides)
        - Includes expectation violations as deterministic context
        - LLM receives judgment, then explains
        - Escalation tone based on blocking conditions
        """
        
        # Sprint 4: Use explicit profile context
        if profile:
            diag_behavior = profile.diagnostics_behavior
            
            # Build profile-aware system prompt
            from .prompt_templates import build_profile_aware_system_prompt
            system_prompt = build_profile_aware_system_prompt(profile)
            
            # Store for LLM call
            self._current_system_prompt = system_prompt
            self._current_profile = profile
            
            logger.info(f"Diagnostics tone: {diag_behavior.tone}, emphasis: {diag_behavior.emphasis}")
            logger.info(f"Reasoning priority order: {profile.reason_taxonomy.diagnostic_priority_order}")
        else:
            logger.warning("No profile context - using default prompts")
            from .prompt_templates import SYSTEM_PROMPT
            self._current_system_prompt = SYSTEM_PROMPT
            self._current_profile = None
        
        # Format snapshot data
        from .prompt_templates import format_snapshot_for_prompt, format_loss_context, format_retrieved_knowledge, DIAGNOSTIC_PROMPT_TEMPLATE
        from .expectation_evaluator import format_expectation_violations
        
        snapshot_formatted = format_snapshot_for_prompt(snapshot, scope, equipment_id)
        
        # Format loss context
        loss_context_formatted = format_loss_context(semantic_signals, scope)
        
        # Format RAG results
        rag_formatted = format_retrieved_knowledge(rag_results)
        
        # Format expectation violations (Sprint 4.5)
        expectations_formatted = ""
        if expectation_result:
            expectations_formatted = format_expectation_violations(expectation_result)
            if expectation_result.escalation_tone:
                expectations_formatted = "\n⚠️  ESCALATION REQUIRED\n" + expectations_formatted
        
        # Build full prompt with expectations
        prompt = DIAGNOSTIC_PROMPT_TEMPLATE.format(
            snapshot_data=snapshot_formatted,
            loss_context=loss_context_formatted,
            retrieved_knowledge=rag_formatted,
            scope=scope,
            equipment_id=equipment_id,
            plant_name=snapshot.get('plant', 'Unknown'),
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Append expectations AFTER standard prompt
        if expectations_formatted:
            prompt += f"\n\n{expectations_formatted}\n\n"
            prompt += "IMPORTANT: The above expectation violations were determined by profile-specific rules. "\n            prompt += "Your role is to EXPLAIN these violations in context, NOT to re-judge them."
        
        return prompt
    
    async def _call_llm(self, prompt: str, profile = None) -> str:
        """
        Call Ollama LLM with the diagnostic prompt.
        
        Sprint 4: Uses profile-aware system prompt (explicit parameter)
        """
        try:
            # Use profile-aware system prompt
            if profile:
                from .prompt_templates import build_profile_aware_system_prompt
                system_prompt = build_profile_aware_system_prompt(profile)
                logger.info(f"Using {profile.display_name} system prompt")
            else:
                # Fallback to stored or default
                system_prompt = getattr(self, '_current_system_prompt', None)
                if not system_prompt:
                    from .prompt_templates import SYSTEM_PROMPT
                    system_prompt = SYSTEM_PROMPT
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "system": system_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,  # Lower temperature for factual output
                            "top_p": 0.9
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get('response', '')
        
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _parse_llm_response(self, llm_response: str) -> Dict:
        """Parse LLM response into structured sections."""
        sections = {
            'what_is_happening': '',
            'why_this_is_happening': '',
            'what_to_do_now': '',
            'what_to_check_next': '',
            'raw_response': llm_response
        }
        
        # Simple section parsing based on headers
        lines = llm_response.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Detect section headers
            if 'what is happening' in line_lower or 'section 1' in line_lower:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'what_is_happening'
                current_content = []
            elif 'why this is happening' in line_lower or 'section 2' in line_lower:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'why_this_is_happening'
                current_content = []
            elif 'what to do now' in line_lower or 'section 3' in line_lower:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'what_to_do_now'
                current_content = []
            elif 'what to check next' in line_lower or 'section 4' in line_lower:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'what_to_check_next'
                current_content = []
            else:
                # Add content to current section
                if current_section and line.strip():
                    current_content.append(line)
        
        # Add final section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _error_response(self, error_message: str) -> Dict:
        """Generate structured error response."""
        return {
            'what_is_happening': f"ERROR: {error_message}",
            'why_this_is_happening': "Cannot generate diagnostic explanation due to missing or invalid data.",
            'what_to_do_now': "Verify that OPC Studio is running and semantic mapping is operational.",
            'what_to_check_next': "1. Check OPC Studio service status\n2. Verify semantic mapping configuration\n3. Ensure runtime data is available",
            'metadata': {
                'error': True,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
