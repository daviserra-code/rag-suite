"""
Semantic Mapping Engine for OPC Studio
YAML-first semantic transformation: Raw OPC UA tags → Stable MES signals

Principles:
1. YAML is source of truth
2. Raw OPC ≠ Semantic signal (explicit mapping)
3. Semantic identifiers are contracts (stable)
4. loss_category is mandatory for operational signals
"""
import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class SemanticEngine:
    """Transforms raw OPC UA signals into semantic MES signals"""
    
    def __init__(self, config_path: str = "/app/config/semantic_mappings.yaml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.station_types: Dict[str, Any] = {}
        self.loss_categories: Dict[str, List[str]] = {}
        self.derived_kpis: List[Dict[str, Any]] = []
        self.load_config()
    
    def load_config(self):
        """Load YAML configuration"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.error(f"Semantic mappings file not found: {self.config_path}")
                return
            
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            
            # Extract key sections
            self.station_types = self.config.get('station_types', {})
            self.loss_categories = self.config.get('loss_categories', {})
            self.derived_kpis = self.config.get('derived_kpis', [])
            
            logger.info(f"Loaded semantic mappings v{self.config.get('version', 'unknown')}")
            logger.info(f"Station types: {len(self.station_types)}, KPIs: {len(self.derived_kpis)}")
            
        except Exception as e:
            logger.error(f"Failed to load semantic mappings: {e}")
            self.config = {}
    
    def get_mappings(self) -> Dict[str, Any]:
        """Get full mapping configuration"""
        return self.config
    
    def get_loss_categories(self) -> Dict[str, List[str]]:
        """Get loss category taxonomy"""
        return self.loss_categories
    
    def get_derived_kpis(self) -> List[Dict[str, Any]]:
        """Get derived KPI definitions"""
        return self.derived_kpis
    
    def map_station_type(self, station_type: str) -> Optional[Dict[str, Any]]:
        """Get semantic signal definitions for a station type"""
        return self.station_types.get(station_type)
    
    def apply_semantic_mapping(
        self,
        raw_data: Dict[str, Any],
        station_type: str,
        station_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform raw OPC UA data into semantic signals
        
        Args:
            raw_data: Dict of OPC tag names to values {tag_name: value}
            station_type: Station type (assembly, welding, testing, robot)
            station_metadata: Optional metadata (station_id, line_id, etc.)
        
        Returns:
            List of semantic signals with loss_category classification
        """
        semantic_signals = []
        
        # Get semantic model for station type
        station_model = self.station_types.get(station_type)
        if not station_model:
            logger.warning(f"No semantic model for station type: {station_type}")
            return self._create_generic_signals(raw_data, station_metadata)
        
        # Process each semantic signal definition
        for signal_def in station_model.get('semantic_signals', []):
            semantic_signal = self._process_signal(signal_def, raw_data, station_metadata)
            if semantic_signal:
                semantic_signals.append(semantic_signal)
        
        return semantic_signals
    
    def _process_signal(
        self,
        signal_def: Dict[str, Any],
        raw_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Process a single semantic signal definition"""
        
        semantic_id = signal_def['semantic_id']
        opc_source = signal_def['opc_source']
        
        # Get raw value from OPC data
        raw_value = raw_data.get(opc_source)
        if raw_value is None:
            return None
        
        # Apply transforms
        value = self._apply_transforms(raw_value, signal_def.get('transforms', []))
        
        # Determine loss category
        loss_category = self._determine_loss_category(value, signal_def)
        
        # Build semantic signal
        semantic_signal = {
            'semantic_id': semantic_id,
            'value': value,
            'unit': signal_def.get('unit'),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source_node': opc_source,
            'loss_category': loss_category,
            'quality': 'good',
            'description': signal_def.get('description', ''),
            'data_type': signal_def.get('data_type', 'unknown')
        }
        
        # Add metadata if provided
        if metadata:
            semantic_signal['metadata'] = metadata
        
        return semantic_signal
    
    def _apply_transforms(self, value: Any, transforms: List[Dict[str, Any]]) -> Any:
        """Apply transform pipeline to raw value"""
        result = value
        
        for transform in transforms:
            transform_type = transform.get('type')
            
            if transform_type == 'range_check':
                min_val = transform.get('min')
                max_val = transform.get('max')
                if min_val is not None and result < min_val:
                    result = min_val
                if max_val is not None and result > max_val:
                    result = max_val
            
            elif transform_type == 'moving_average':
                # Placeholder - would need historical data
                pass
            
            elif transform_type == 'scale':
                factor = transform.get('factor', 1.0)
                result = result * factor
            
            elif transform_type == 'offset':
                offset = transform.get('offset', 0.0)
                result = result + offset
        
        return result
    
    def _determine_loss_category(
        self,
        value: Any,
        signal_def: Dict[str, Any]
    ) -> Optional[str]:
        """Determine loss category based on signal definition and value"""
        
        # Check for direct loss_category
        if 'loss_category' in signal_def:
            return signal_def['loss_category']
        
        # Check for state-based mapping
        if 'loss_category_map' in signal_def:
            loss_map = signal_def['loss_category_map']
            return loss_map.get(value)
        
        # Check for rule-based category
        if 'loss_category_rule' in signal_def:
            rule = signal_def['loss_category_rule']
            condition = rule.get('condition', '')
            category = rule.get('category')
            
            # Simple condition evaluation
            if self._evaluate_condition(condition, value):
                return category
        
        return None
    
    def _evaluate_condition(self, condition: str, value: Any) -> bool:
        """Evaluate simple condition string"""
        try:
            # Replace 'value' with actual value in condition
            condition_str = condition.replace('value', str(value))
            return eval(condition_str)
        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False
    
    def _create_generic_signals(
        self,
        raw_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create generic semantic signals for unknown station types"""
        signals = []
        
        for tag_name, value in raw_data.items():
            signal = {
                'semantic_id': f'raw.{tag_name.lower()}',
                'value': value,
                'unit': None,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source_node': tag_name,
                'loss_category': None,
                'quality': 'good',
                'description': f'Raw tag: {tag_name}',
                'data_type': type(value).__name__
            }
            
            if metadata:
                signal['metadata'] = metadata
            
            signals.append(signal)
        
        return signals
    
    def calculate_kpis(
        self,
        semantic_signals: List[Dict[str, Any]],
        historical_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Calculate derived KPIs from semantic signals"""
        kpis = []
        
        # Build signal lookup
        signal_values = {s['semantic_id']: s['value'] for s in semantic_signals}
        
        for kpi_def in self.derived_kpis:
            kpi = self._calculate_kpi(kpi_def, signal_values, historical_data)
            if kpi:
                kpis.append(kpi)
        
        return kpis
    
    def _calculate_kpi(
        self,
        kpi_def: Dict[str, Any],
        signal_values: Dict[str, Any],
        historical_data: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Calculate a single KPI"""
        
        kpi_id = kpi_def['kpi_id']
        formula = kpi_def.get('formula', '')
        dependencies = kpi_def.get('dependencies', [])
        
        # Check if all dependencies are available
        for dep in dependencies:
            if dep not in signal_values:
                logger.debug(f"KPI {kpi_id}: missing dependency {dep}")
                return None
        
        # Placeholder: Simple KPI calculations
        # In production, would use proper formula parser
        value = None
        
        if kpi_id == 'oee.availability':
            # Simplified - would need historical state data
            state = signal_values.get('station.state')
            value = 100.0 if state == 'RUNNING' else 0.0
        
        elif kpi_id == 'oee.quality':
            quality_ok = signal_values.get('station.quality_ok', 0)
            parts_count = signal_values.get('station.parts_count', 1)
            value = (quality_ok / parts_count * 100) if parts_count > 0 else 100.0
        
        elif kpi_id == 'throughput.actual':
            parts = signal_values.get('station.parts_count', 0)
            # Simplified - would need time tracking
            value = parts * 1.0  # parts per current period
        
        if value is None:
            return None
        
        return {
            'kpi_id': kpi_id,
            'value': value,
            'unit': kpi_def.get('unit', ''),
            'target': kpi_def.get('target'),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'description': kpi_def.get('description', ''),
            'formula': formula
        }
    
    def validate_semantic_signals(
        self,
        signals: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Validate semantic signals against rules"""
        
        validation_rules = self.config.get('validation', [])
        errors = []
        warnings = []
        
        # Check for required station.state
        has_state = any(s['semantic_id'] == 'station.state' for s in signals)
        if not has_state:
            errors.append("Missing required signal: station.state")
        
        # Check loss_category for non-running states
        for signal in signals:
            if signal['semantic_id'] == 'station.state':
                if signal['value'] != 'RUNNING' and not signal['loss_category']:
                    errors.append(
                        f"State {signal['value']} must have loss_category"
                    )
        
        # Check numeric ranges
        for signal in signals:
            if signal['data_type'] in ['float', 'integer']:
                # Would check against defined ranges in YAML
                pass
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_station_type_from_metadata(self, metadata: Dict[str, Any]) -> str:
        """Infer station type from metadata"""
        
        # Check explicit type field
        if 'type' in metadata:
            return metadata['type']
        
        # Infer from station name/ID
        station_name = metadata.get('name', '').lower()
        
        if 'assembly' in station_name:
            return 'assembly'
        elif 'weld' in station_name:
            return 'welding'
        elif 'test' in station_name or 'inspect' in station_name:
            return 'testing'
        elif 'robot' in station_name:
            return 'robot'
        
        return 'generic'


# Global instance
_semantic_engine = None


def get_semantic_engine() -> SemanticEngine:
    """Get or create global semantic engine instance"""
    global _semantic_engine
    if _semantic_engine is None:
        _semantic_engine = SemanticEngine()
    return _semantic_engine
