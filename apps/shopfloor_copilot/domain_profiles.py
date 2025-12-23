"""
Domain Profile Management
Sprint 4 — Material Intelligence & Domain Profiles

Provides runtime-switchable domain profiles for:
- Aerospace & Defence (strictest)
- Pharma / Process (batch-centric)
- Automotive / Discrete (throughput-focused)

DESIGN PRINCIPLES:
- Single codebase, configuration-driven
- No industry-specific forks
- Profiles configure behavior, not logic
- Read-only, audit-first posture
"""

import os
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass


@dataclass
class MaterialModel:
    """Material traceability configuration"""
    identification: str  # serial | lot
    genealogy_depth: str  # shallow | deep
    revision_required: bool
    expiry_management: str  # mandatory | conditional | none
    traceability_level: str  # serial | lot | batch | none
    material_mandatory_fields: List[str]


@dataclass
class EquipmentModel:
    """Equipment certification and calibration config"""
    certification_required: bool
    tooling_calibration_required: bool
    maintenance_log_mandatory: bool
    qualification_tracking: bool
    calibration_mandatory_fields: List[str]


@dataclass
class ProcessConstraints:
    """Process compliance and quality gate config"""
    deviation_required_for_exceptions: bool
    operator_certification_required: bool
    documentation_signoff_required: bool
    work_instruction_mandatory: bool
    quality_gate_enforcement: str  # strict | moderate | loose
    change_control_required: bool


@dataclass
class ReasonTaxonomy:
    """Reason categorization configuration"""
    enabled: List[str]  # Level 1 categories enabled for this profile
    diagnostic_priority_order: List[str]  # Evaluation order for diagnostics
    subcategories: Dict[str, List[str]]  # Level 2 subcategories per category


@dataclass
class RAGPreferences:
    """RAG retrieval preferences"""
    priority_sources: List[str]
    search_weights: Dict[str, float]


@dataclass
class UIEmphasis:
    """UI display preferences"""
    primary_views: List[str]
    warning_thresholds: Dict[str, int]
    color_coding: Dict[str, str]


@dataclass
class DiagnosticsBehavior:
    """AI diagnostics behavior configuration"""
    tone: str  # formal | pragmatic
    emphasis: str  # compliance_first | quality_first | throughput_first
    include_documentation_refs: bool
    reasoning_style: str  # audit_ready | gmp_compliant | lean_focused
    output_template: str  # aerospace | pharma | automotive


@dataclass
class ProfileExpectations:
    """Domain-specific expectations and escalation rules"""
    # Binary expectations (True = requires escalation/authorization)
    zero_output_requires_authorization: bool = False
    zero_output_requires_batch_context: bool = False
    zero_output_allowed_during_startup: bool = False
    zero_output_allowed_during_changeover: bool = False
    
    reduced_speed_requires_justification: bool = False
    reduced_speed_requires_deviation: bool = False
    reduced_speed_common_during_rampup: bool = False
    
    critical_station_requires_evidence: bool = False
    dry_run_must_be_declared: bool = False
    unauthorized_stop_is_violation: bool = False
    missing_serial_binding_is_blocking: bool = False
    environmental_excursion_is_blocking: bool = False
    missing_batch_record_is_violation: bool = False
    unauthorized_parameter_change_is_blocking: bool = False
    minor_stops_expected_in_normal_operation: bool = False
    blocking_only_for_safety: bool = False
    
    # Thresholds
    zero_output_duration_threshold_minutes: int = 15
    speed_reduction_threshold_percent: int = 20
    
    # Lists
    critical_stations: List[str] = None
    environmental_limits: Dict[str, float] = None
    
    def __post_init__(self):
        if self.critical_stations is None:
            self.critical_stations = []
        if self.environmental_limits is None:
            self.environmental_limits = {}


@dataclass
class ExpectationResult:
    """Result of profile expectation evaluation"""
    violated_expectations: List[str]
    warnings: List[str]
    blocking_conditions: List[str]
    requires_human_confirmation: bool
    severity: str  # normal | warning | critical
    escalation_tone: bool  # True if diagnostics should use escalation language


@dataclass
class DomainProfile:
    """Complete domain profile"""
    name: str
    display_name: str
    description: str
    material_model: MaterialModel
    equipment_model: EquipmentModel
    process_constraints: ProcessConstraints
    reason_taxonomy: ReasonTaxonomy
    rag_preferences: RAGPreferences
    ui_emphasis: UIEmphasis
    diagnostics_behavior: DiagnosticsBehavior
    profile_expectations: ProfileExpectations


class DomainProfileManager:
    """
    Manages domain profile loading and switching.
    
    Thread-safe singleton for profile management across the application.
    """
    
    _instance = None
    _config_file = None
    _active_profile: Optional[DomainProfile] = None
    _profiles: Dict[str, DomainProfile] = {}
    _migration_map: Dict[str, Dict[str, str]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize profile manager (loads config on first instantiation)"""
        if not self._profiles:
            self._load_config()
    
    def _load_config(self):
        """Load domain profiles from YAML configuration"""
        # Find domain_profile.yml
        config_path = Path(__file__).parent / "domain_profile.yml"
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Domain profile configuration not found: {config_path}"
            )
        
        self._config_file = config_path
        
        # Load YAML
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Load migration mappings
        if 'migration' in config:
            self._migration_map = config['migration'].get('loss_category_to_reason', {})
        
        # Parse profiles
        profiles_config = config.get('profiles', {})
        active_profile_name = config.get('active_profile', 'aerospace_defence')
        
        for profile_name, profile_data in profiles_config.items():
            profile = self._parse_profile(profile_name, profile_data)
            self._profiles[profile_name] = profile
        
        # Set active profile
        if active_profile_name in self._profiles:
            self._active_profile = self._profiles[active_profile_name]
        else:
            # Fallback to first available profile
            self._active_profile = list(self._profiles.values())[0]
        
        print(f"✅ Domain profiles loaded: {len(self._profiles)} profiles")
        print(f"   Active profile: {self._active_profile.display_name}")
    
    def _parse_profile(self, name: str, data: Dict[str, Any]) -> DomainProfile:
        """Parse profile configuration into DomainProfile dataclass"""
        
        # Material model
        material_data = data.get('material_model', {})
        material_model = MaterialModel(
            identification=material_data.get('identification', 'lot'),
            genealogy_depth=material_data.get('genealogy_depth', 'shallow'),
            revision_required=material_data.get('revision_required', False),
            expiry_management=material_data.get('expiry_management', 'none'),
            traceability_level=material_data.get('traceability_level', 'lot'),
            material_mandatory_fields=material_data.get('material_mandatory_fields', [])
        )
        
        # Equipment model
        equipment_data = data.get('equipment_model', {})
        equipment_model = EquipmentModel(
            certification_required=equipment_data.get('certification_required', False),
            tooling_calibration_required=equipment_data.get('tooling_calibration_required', False),
            maintenance_log_mandatory=equipment_data.get('maintenance_log_mandatory', False),
            qualification_tracking=equipment_data.get('qualification_tracking', False),
            calibration_mandatory_fields=equipment_data.get('calibration_mandatory_fields', [])
        )
        
        # Process constraints
        process_data = data.get('process_constraints', {})
        process_constraints = ProcessConstraints(
            deviation_required_for_exceptions=process_data.get('deviation_required_for_exceptions', False),
            operator_certification_required=process_data.get('operator_certification_required', False),
            documentation_signoff_required=process_data.get('documentation_signoff_required', False),
            work_instruction_mandatory=process_data.get('work_instruction_mandatory', False),
            quality_gate_enforcement=process_data.get('quality_gate_enforcement', 'moderate'),
            change_control_required=process_data.get('change_control_required', False)
        )
        
        # Reason taxonomy
        taxonomy_data = data.get('reason_taxonomy', {})
        reason_taxonomy = ReasonTaxonomy(
            enabled=taxonomy_data.get('enabled', []),
            diagnostic_priority_order=taxonomy_data.get('diagnostic_priority_order', taxonomy_data.get('enabled', [])),
            subcategories=taxonomy_data.get('subcategories', {})
        )
        
        # RAG preferences
        rag_data = data.get('rag_preferences', {})
        rag_preferences = RAGPreferences(
            priority_sources=rag_data.get('priority_sources', []),
            search_weights=rag_data.get('search_weights', {})
        )
        
        # UI emphasis
        ui_data = data.get('ui_emphasis', {})
        ui_emphasis = UIEmphasis(
            primary_views=ui_data.get('primary_views', []),
            warning_thresholds=ui_data.get('warning_thresholds', {}),
            color_coding=ui_data.get('color_coding', {})
        )
        
        # Diagnostics behavior
        diag_data = data.get('diagnostics_behavior', {})
        diagnostics_behavior = DiagnosticsBehavior(
            tone=diag_data.get('tone', 'pragmatic'),
            emphasis=diag_data.get('emphasis', 'throughput_first'),
            include_documentation_refs=diag_data.get('include_documentation_refs', False),
            reasoning_style=diag_data.get('reasoning_style', 'lean_focused'),
            output_template=diag_data.get('output_template', 'automotive')
        )
        
        # Profile expectations
        expect_data = data.get('profile_expectations', {})
        profile_expectations = ProfileExpectations(
            zero_output_requires_authorization=expect_data.get('zero_output_requires_authorization', False),
            zero_output_requires_batch_context=expect_data.get('zero_output_requires_batch_context', False),
            zero_output_allowed_during_startup=expect_data.get('zero_output_allowed_during_startup', False),
            zero_output_allowed_during_changeover=expect_data.get('zero_output_allowed_during_changeover', False),
            reduced_speed_requires_justification=expect_data.get('reduced_speed_requires_justification', False),
            reduced_speed_requires_deviation=expect_data.get('reduced_speed_requires_deviation', False),
            reduced_speed_common_during_rampup=expect_data.get('reduced_speed_common_during_rampup', False),
            critical_station_requires_evidence=expect_data.get('critical_station_requires_evidence', False),
            dry_run_must_be_declared=expect_data.get('dry_run_must_be_declared', False),
            unauthorized_stop_is_violation=expect_data.get('unauthorized_stop_is_violation', False),
            missing_serial_binding_is_blocking=expect_data.get('missing_serial_binding_is_blocking', False),
            environmental_excursion_is_blocking=expect_data.get('environmental_excursion_is_blocking', False),
            missing_batch_record_is_violation=expect_data.get('missing_batch_record_is_violation', False),
            unauthorized_parameter_change_is_blocking=expect_data.get('unauthorized_parameter_change_is_blocking', False),
            minor_stops_expected_in_normal_operation=expect_data.get('minor_stops_expected_in_normal_operation', False),
            blocking_only_for_safety=expect_data.get('blocking_only_for_safety', False),
            zero_output_duration_threshold_minutes=expect_data.get('zero_output_duration_threshold_minutes', 15),
            speed_reduction_threshold_percent=expect_data.get('speed_reduction_threshold_percent', 20),
            critical_stations=expect_data.get('critical_stations', []),
            environmental_limits=expect_data.get('environmental_limits', {})
        )
        
        return DomainProfile(
            name=name,
            display_name=data.get('display_name', name),
            description=data.get('description', ''),
            material_model=material_model,
            equipment_model=equipment_model,
            process_constraints=process_constraints,
            reason_taxonomy=reason_taxonomy,
            rag_preferences=rag_preferences,
            ui_emphasis=ui_emphasis,
            diagnostics_behavior=diagnostics_behavior,
            profile_expectations=profile_expectations
        )
    
    def get_active_profile(self) -> DomainProfile:
        """Get the currently active domain profile"""
        if not self._active_profile:
            self._load_config()
        return self._active_profile
    
    def get_profile(self, name: str) -> Optional[DomainProfile]:
        """Get a specific profile by name"""
        return self._profiles.get(name)
    
    def list_profiles(self) -> List[str]:
        """List all available profile names"""
        return list(self._profiles.keys())
    
    def list_profiles_detailed(self) -> List[Dict[str, str]]:
        """List all profiles with display names and descriptions"""
        return [
            {
                'name': profile.name,
                'display_name': profile.display_name,
                'description': profile.description,
                'active': profile.name == self._active_profile.name
            }
            for profile in self._profiles.values()
        ]
    
    def switch_profile(self, profile_name: str) -> bool:
        """
        Switch to a different domain profile at runtime.
        
        Args:
            profile_name: Name of the profile to activate
            
        Returns:
            True if successful, False if profile not found
        """
        if profile_name not in self._profiles:
            print(f"❌ Profile '{profile_name}' not found")
            return False
        
        old_profile = self._active_profile.display_name
        self._active_profile = self._profiles[profile_name]
        
        print(f"✅ Profile switched: {old_profile} → {self._active_profile.display_name}")
        return True
    
    def migrate_loss_category(self, loss_category: str) -> Dict[str, str]:
        """
        Migrate Sprint 1-3 loss_category to new reason taxonomy.
        
        Args:
            loss_category: Legacy loss category (e.g., "availability.equipment_failure")
            
        Returns:
            Dict with reason_category and reason_subcategory
        """
        if loss_category in self._migration_map:
            return self._migration_map[loss_category]
        
        # Fallback: try to extract category from pattern
        if '.' in loss_category:
            parts = loss_category.split('.')
            return {
                'reason_category': 'equipment',  # Default fallback
                'reason_subcategory': parts[1] if len(parts) > 1 else 'unknown'
            }
        
        return {
            'reason_category': 'process',
            'reason_subcategory': 'unknown'
        }
    
    def validate_reason(self, category: str, subcategory: Optional[str] = None) -> bool:
        """
        Validate if a reason category/subcategory is valid for active profile.
        
        Args:
            category: Level 1 reason category (e.g., 'equipment')
            subcategory: Optional Level 2 subcategory (e.g., 'breakdown')
            
        Returns:
            True if valid for current profile
        """
        profile = self.get_active_profile()
        
        # Check Level 1
        if category not in profile.reason_taxonomy.enabled:
            return False
        
        # Check Level 2 if provided
        if subcategory:
            valid_subcategories = profile.reason_taxonomy.subcategories.get(category, [])
            return subcategory in valid_subcategories
        
        return True
    
    def get_rag_weight(self, source_type: str) -> float:
        """
        Get RAG search weight for a source type based on active profile.
        
        Args:
            source_type: Type of document source (e.g., 'work_instructions')
            
        Returns:
            Weight multiplier (default 1.0)
        """
        profile = self.get_active_profile()
        return profile.rag_preferences.search_weights.get(source_type, 1.0)
    
    def is_material_field_required(self, field_name: str) -> bool:
        """Check if a material field is mandatory for active profile"""
        profile = self.get_active_profile()
        return field_name in profile.material_model.material_mandatory_fields
    
    def is_calibration_field_required(self, field_name: str) -> bool:
        """Check if a calibration field is mandatory for active profile"""
        profile = self.get_active_profile()
        return field_name in profile.equipment_model.calibration_mandatory_fields


# Global singleton instance
_profile_manager = DomainProfileManager()


def get_active_profile() -> DomainProfile:
    """Get the currently active domain profile (convenience function)"""
    return _profile_manager.get_active_profile()


def switch_profile(profile_name: str) -> bool:
    """Switch to a different domain profile (convenience function)"""
    return _profile_manager.switch_profile(profile_name)


def list_profiles() -> List[Dict[str, str]]:
    """List all available profiles (convenience function)"""
    return _profile_manager.list_profiles_detailed()


def migrate_loss_category(loss_category: str) -> Dict[str, str]:
    """Migrate legacy loss_category to reason taxonomy (convenience function)"""
    return _profile_manager.migrate_loss_category(loss_category)


def get_rag_weight(source_type: str) -> float:
    """Get RAG search weight for source type (convenience function)"""
    return _profile_manager.get_rag_weight(source_type)


# Expose manager for advanced use
profile_manager = _profile_manager
