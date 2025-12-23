"""
Reason Taxonomy System
Sprint 4 — Material Intelligence & Domain Profiles

REPLACES Sprint 1-3 loss_category with 2-level taxonomy:
- Level 1: Universal categories (equipment, material, process, quality, etc.)
- Level 2: Profile-dependent subcategories

DESIGN PRINCIPLES:
- Single taxonomy, profile determines enabled categories
- Backward compatible with loss_category via migration mapping
- Deterministic and explainable (no AI hallucination)
- Read-only observation, not control logic

MIGRATION STRATEGY:
- Existing loss_category data migrates via mapping in domain_profile.yml
- New code uses reason_category + reason_subcategory
- Both can coexist during transition period
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from enum import Enum


class OEEImpact(str, Enum):
    """OEE pillar impacted by reason"""
    AVAILABILITY = "availability"  # Machine down
    PERFORMANCE = "performance"    # Running slow
    QUALITY = "quality"            # Making bad parts
    NONE = "none"                  # Non-productive time


class ReasonSeverity(str, Enum):
    """Severity level of the reason"""
    CRITICAL = "critical"      # Immediate action required
    WARNING = "warning"        # Attention needed
    INFO = "info"              # Informational
    NORMAL = "normal"          # Expected/planned


@dataclass
class ReasonCategory:
    """
    Level 1 reason category (universal across all domains).
    
    Examples: equipment, material, process, quality, documentation, people, tooling
    """
    category: str                       # Category identifier
    display_name: str                   # Human-readable name
    description: str                    # Category description
    oee_impact: OEEImpact              # Which OEE pillar this affects
    icon: Optional[str] = None         # UI icon name
    color: Optional[str] = None        # UI color code
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'category': self.category,
            'display_name': self.display_name,
            'description': self.description,
            'oee_impact': self.oee_impact.value,
            'icon': self.icon,
            'color': self.color
        }


@dataclass
class ReasonSubcategory:
    """
    Level 2 reason subcategory (profile-dependent).
    
    Examples: 
    - equipment.breakdown
    - material.shortage
    - quality.defect_detected
    """
    parent_category: str                # Parent Level 1 category
    subcategory: str                    # Subcategory identifier
    display_name: str                   # Human-readable name
    description: Optional[str] = None   # Optional description
    severity: ReasonSeverity = ReasonSeverity.WARNING
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'parent_category': self.parent_category,
            'subcategory': self.subcategory,
            'display_name': self.display_name,
            'description': self.description,
            'severity': self.severity.value
        }


@dataclass
class ReasonInstance:
    """
    Actual reason recorded for a specific event.
    
    Links a runtime event to the taxonomy with context.
    """
    reason_id: str                      # Unique identifier
    reason_category: str                # Level 1 category
    reason_subcategory: Optional[str]   # Level 2 subcategory
    
    # Context
    event_id: Optional[str] = None      # Associated event (downtime, quality, etc.)
    station_id: Optional[str] = None
    line_id: Optional[str] = None
    work_order: Optional[str] = None
    
    # Evidence
    value: Optional[float] = None       # Numeric value if applicable
    unit: Optional[str] = None          # Unit of value
    threshold: Optional[float] = None   # Threshold that was exceeded
    
    # Metadata
    timestamp: Optional[str] = None
    operator: Optional[str] = None
    notes: Optional[str] = None
    
    # Migration support (backward compatibility)
    legacy_loss_category: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'reason_id': self.reason_id,
            'reason_category': self.reason_category,
            'reason_subcategory': self.reason_subcategory,
            'event_id': self.event_id,
            'station_id': self.station_id,
            'line_id': self.line_id,
            'work_order': self.work_order,
            'value': self.value,
            'unit': self.unit,
            'threshold': self.threshold,
            'timestamp': self.timestamp,
            'operator': self.operator,
            'notes': self.notes,
            'legacy_loss_category': self.legacy_loss_category
        }
    
    def get_full_reason(self) -> str:
        """Get full reason string (category.subcategory)"""
        if self.reason_subcategory:
            return f"{self.reason_category}.{self.reason_subcategory}"
        return self.reason_category


# =============================================================================
# UNIVERSAL REASON CATEGORIES (Level 1)
# Valid across all domains, profile determines which are enabled
# =============================================================================

UNIVERSAL_CATEGORIES = {
    'equipment': ReasonCategory(
        category='equipment',
        display_name='Equipment',
        description='Equipment-related issues (machines, tools, fixtures)',
        oee_impact=OEEImpact.AVAILABILITY,
        icon='settings',
        color='#ef4444'  # Red
    ),
    'material': ReasonCategory(
        category='material',
        display_name='Material',
        description='Material availability, quality, or specification issues',
        oee_impact=OEEImpact.AVAILABILITY,
        icon='inventory',
        color='#f59e0b'  # Amber
    ),
    'process': ReasonCategory(
        category='process',
        display_name='Process',
        description='Process parameters, procedures, or control issues',
        oee_impact=OEEImpact.PERFORMANCE,
        icon='speed',
        color='#8b5cf6'  # Purple
    ),
    'quality': ReasonCategory(
        category='quality',
        display_name='Quality',
        description='Quality defects, inspection failures, or non-conformance',
        oee_impact=OEEImpact.QUALITY,
        icon='verified',
        color='#ec4899'  # Pink
    ),
    'documentation': ReasonCategory(
        category='documentation',
        display_name='Documentation',
        description='Missing, outdated, or incomplete documentation',
        oee_impact=OEEImpact.AVAILABILITY,
        icon='description',
        color='#6366f1'  # Indigo
    ),
    'people': ReasonCategory(
        category='people',
        display_name='People',
        description='Operator-related issues (absence, training, certification)',
        oee_impact=OEEImpact.AVAILABILITY,
        icon='person',
        color='#10b981'  # Green
    ),
    'tooling': ReasonCategory(
        category='tooling',
        display_name='Tooling',
        description='Tooling-specific issues (calibration, damage, availability)',
        oee_impact=OEEImpact.AVAILABILITY,
        icon='build',
        color='#3b82f6'  # Blue
    ),
    'logistics': ReasonCategory(
        category='logistics',
        display_name='Logistics',
        description='Material flow, upstream/downstream dependencies',
        oee_impact=OEEImpact.AVAILABILITY,
        icon='local_shipping',
        color='#14b8a6'  # Teal
    ),
    'environmental': ReasonCategory(
        category='environmental',
        display_name='Environmental',
        description='Environmental conditions (cleanroom, temperature, humidity)',
        oee_impact=OEEImpact.AVAILABILITY,
        icon='thermostat',
        color='#06b6d4'  # Cyan
    )
}


class ReasonTaxonomyManager:
    """
    Manages reason taxonomy and validation against active domain profile.
    
    Provides:
    - Reason validation (is this valid for current profile?)
    - Migration from legacy loss_category
    - Hierarchy traversal
    - Filtering by profile
    """
    
    def __init__(self):
        """Initialize taxonomy manager"""
        from ..domain_profiles import profile_manager
        self.profile_manager = profile_manager
    
    def get_enabled_categories(self) -> List[ReasonCategory]:
        """Get Level 1 categories enabled for active profile"""
        profile = self.profile_manager.get_active_profile()
        enabled = profile.reason_taxonomy.enabled
        
        return [
            UNIVERSAL_CATEGORIES[cat]
            for cat in enabled
            if cat in UNIVERSAL_CATEGORIES
        ]
    
    def get_subcategories(self, category: str) -> List[str]:
        """Get Level 2 subcategories for a category in active profile"""
        profile = self.profile_manager.get_active_profile()
        return profile.reason_taxonomy.subcategories.get(category, [])
    
    def is_valid_reason(self, category: str, subcategory: Optional[str] = None) -> bool:
        """
        Validate if reason is valid for active profile.
        
        Args:
            category: Level 1 category (e.g., 'equipment')
            subcategory: Optional Level 2 subcategory (e.g., 'breakdown')
            
        Returns:
            True if valid for current profile
        """
        return self.profile_manager.validate_reason(category, subcategory)
    
    def migrate_from_loss_category(self, loss_category: str) -> Tuple[str, Optional[str]]:
        """
        Migrate Sprint 1-3 loss_category to new reason taxonomy.
        
        Args:
            loss_category: Legacy loss category (e.g., 'availability.equipment_failure')
            
        Returns:
            (reason_category, reason_subcategory)
        """
        mapping = self.profile_manager.migrate_loss_category(loss_category)
        return (
            mapping.get('reason_category', 'process'),
            mapping.get('reason_subcategory')
        )
    
    def create_reason_instance(
        self,
        category: str,
        subcategory: Optional[str] = None,
        **kwargs
    ) -> ReasonInstance:
        """
        Create a reason instance with validation.
        
        Validates against active profile before creating.
        """
        if not self.is_valid_reason(category, subcategory):
            raise ValueError(
                f"Reason '{category}.{subcategory}' not valid for current profile"
            )
        
        return ReasonInstance(
            reason_id=kwargs.get('reason_id', f"{category}_{subcategory}_{kwargs.get('timestamp', '')}"),
            reason_category=category,
            reason_subcategory=subcategory,
            event_id=kwargs.get('event_id'),
            station_id=kwargs.get('station_id'),
            line_id=kwargs.get('line_id'),
            work_order=kwargs.get('work_order'),
            value=kwargs.get('value'),
            unit=kwargs.get('unit'),
            threshold=kwargs.get('threshold'),
            timestamp=kwargs.get('timestamp'),
            operator=kwargs.get('operator'),
            notes=kwargs.get('notes'),
            legacy_loss_category=kwargs.get('legacy_loss_category')
        )
    
    def get_category_info(self, category: str) -> Optional[ReasonCategory]:
        """Get detailed information about a Level 1 category"""
        return UNIVERSAL_CATEGORIES.get(category)
    
    def get_oee_impact(self, category: str) -> OEEImpact:
        """Get OEE impact for a reason category"""
        cat_info = self.get_category_info(category)
        return cat_info.oee_impact if cat_info else OEEImpact.NONE
    
    def filter_reasons_by_oee_pillar(
        self,
        oee_pillar: OEEImpact
    ) -> List[ReasonCategory]:
        """Get all enabled categories that impact a specific OEE pillar"""
        enabled_cats = self.get_enabled_categories()
        return [
            cat for cat in enabled_cats
            if cat.oee_impact == oee_pillar
        ]
    
    def get_taxonomy_tree(self) -> Dict:
        """
        Get complete taxonomy tree for active profile.
        
        Returns nested dictionary structure:
        {
            'category': {
                'info': {...},
                'subcategories': [...]
            }
        }
        """
        profile = self.profile_manager.get_active_profile()
        enabled_cats = self.get_enabled_categories()
        
        tree = {}
        for cat in enabled_cats:
            tree[cat.category] = {
                'info': cat.to_dict(),
                'subcategories': self.get_subcategories(cat.category)
            }
        
        return tree


# Global singleton instance
_taxonomy_manager = ReasonTaxonomyManager()


def get_enabled_categories() -> List[ReasonCategory]:
    """Get enabled reason categories for active profile (convenience function)"""
    return _taxonomy_manager.get_enabled_categories()


def is_valid_reason(category: str, subcategory: Optional[str] = None) -> bool:
    """Validate reason against active profile (convenience function)"""
    return _taxonomy_manager.is_valid_reason(category, subcategory)


def migrate_from_loss_category(loss_category: str) -> Tuple[str, Optional[str]]:
    """Migrate legacy loss_category to reason taxonomy (convenience function)"""
    return _taxonomy_manager.migrate_from_loss_category(loss_category)


def create_reason_instance(
    category: str,
    subcategory: Optional[str] = None,
    **kwargs
) -> ReasonInstance:
    """Create a validated reason instance (convenience function)"""
    return _taxonomy_manager.create_reason_instance(category, subcategory, **kwargs)


# Expose manager for advanced use
taxonomy_manager = _taxonomy_manager
