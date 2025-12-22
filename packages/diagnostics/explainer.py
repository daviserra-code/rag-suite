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
        equipment_id: str
    ) -> Dict[str, Any]:
        """
        Generate structured, explainable diagnostic for a line or station.
        
        Args:
            scope: "line" or "station"
            equipment_id: Line ID (e.g., "A01") or Station ID (e.g., "ST18")
        
        Returns:
            Structured diagnostic with 4 sections:
            - what_is_happening: Runtime evidence
            - why_this_is_happening: Reasoned explanation
            - what_to_do_now: Procedures from RAG
            - what_to_check_next: Actionable checklist
        """
        try:
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
            
            # Step 3: Identify active loss_category
            loss_context = self._extract_loss_context(semantic_signals, scope)
            
            # Step 4: Query RAG knowledge base
            logger.info(f"Querying RAG for {scope} {equipment_id}")
            rag_results = await self._query_rag(
                equipment_id=equipment_id,
                loss_categories=[lc['category'] for lc in loss_context.get('active_losses', [])],
                scope=scope
            )
            
            # Step 5: Build structured prompt
            prompt = self._build_diagnostic_prompt(
                snapshot=snapshot,
                semantic_signals=semantic_signals,
                loss_context=loss_context,
                rag_results=rag_results,
                scope=scope,
                equipment_id=equipment_id
            )
            
            # Step 6: Call LLM
            logger.info("Calling LLM for diagnostic generation")
            llm_response = await self._call_llm(prompt)
            
            # Step 7: Parse and structure response
            structured_response = self._parse_llm_response(llm_response)
            
            # Step 8: Add metadata
            structured_response['metadata'] = {
                'scope': scope,
                'equipment_id': equipment_id,
                'timestamp': datetime.utcnow().isoformat(),
                'plant': snapshot.get('plant', 'Unknown'),
                'model': self.model_name,
                'loss_categories': [lc['category'] for lc in loss_context.get('active_losses', [])],
                'rag_documents': len(rag_results)
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
    
    def _extract_loss_context(self, semantic_signals: Optional[Dict], scope: str) -> Dict:
        """Extract active loss categories from semantic signals."""
        if not semantic_signals:
            return {
                'active_losses': [],
                'availability_affected': False,
                'performance_affected': False,
                'quality_affected': False
            }
        
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
        
        return {
            'active_losses': active_losses,
            'availability_affected': availability_affected,
            'performance_affected': performance_affected,
            'quality_affected': quality_affected
        }
    
    async def _query_rag(
        self,
        equipment_id: str,
        loss_categories: List[str],
        scope: str
    ) -> List[Dict]:
        """Query Chroma for relevant procedures and documentation."""
        if not CHROMA_AVAILABLE:
            logger.warning("Chroma client not available")
            return []
        
        try:
            # Build search query
            query_parts = [equipment_id]
            
            # Add loss category keywords
            for category in loss_categories:
                # Extract specific loss type (e.g., "equipment_failure" from "availability.equipment_failure")
                if '.' in category:
                    loss_type = category.split('.')[-1].replace('_', ' ')
                    query_parts.append(loss_type)
            
            query_text = ' '.join(query_parts)
            
            # Use existing Chroma client infrastructure
            collection = get_collection("shopfloor_docs")
            
            # Query with metadata filter
            results = collection.query(
                query_texts=[query_text],
                n_results=5,
                where={
                    "$or": [
                        {"doc_type": "work_instruction"},
                        {"doc_type": "sop"},
                        {"doc_type": "maintenance_log"}
                    ]
                }
            )
            
            # Format results
            documents = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            distances = results.get('distances', [[]])[0]
            
            return [
                {
                    'document': doc,
                    'metadata': meta,
                    'score': 1.0 - dist  # Convert distance to similarity
                }
                for doc, meta, dist in zip(documents, metadatas, distances)
                if dist < 1.5  # Filter by similarity threshold
            ]
        
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
        equipment_id: str
    ) -> str:
        """Build the structured diagnostic prompt."""
        
        # Format snapshot data
        snapshot_formatted = format_snapshot_for_prompt(snapshot, scope, equipment_id)
        
        # Format loss context
        loss_context_formatted = format_loss_context(semantic_signals, scope)
        
        # Format RAG results
        rag_formatted = format_retrieved_knowledge(rag_results)
        
        # Build full prompt
        prompt = DIAGNOSTIC_PROMPT_TEMPLATE.format(
            snapshot_data=snapshot_formatted,
            loss_context=loss_context_formatted,
            retrieved_knowledge=rag_formatted,
            scope=scope,
            equipment_id=equipment_id,
            plant_name=snapshot.get('plant', 'Unknown'),
            timestamp=datetime.utcnow().isoformat()
        )
        
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """Call Ollama LLM with the diagnostic prompt."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "system": SYSTEM_PROMPT,
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
