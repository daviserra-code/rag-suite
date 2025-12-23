"""
Models package initialization
Sprint 4 — Material Intelligence & Domain Profiles
"""

from .material_core import (
    MaterialDefinition,
    MaterialInstance,
    MaterialState,
    QualityStatus,
    GenealogyLink,
    MaterialGenealogyTree,
    create_material_instance,
    validate_material_for_profile
)

from .reason_taxonomy import (
    ReasonCategory,
    ReasonSubcategory,
    ReasonInstance,
    OEEImpact,
    ReasonSeverity,
    get_enabled_categories,
    is_valid_reason,
    migrate_from_loss_category,
    create_reason_instance,
    taxonomy_manager
)

__all__ = [
    # Material core
    'MaterialDefinition',
    'MaterialInstance',
    'MaterialState',
    'QualityStatus',
    'GenealogyLink',
    'MaterialGenealogyTree',
    'create_material_instance',
    'validate_material_for_profile',
    # Reason taxonomy
    'ReasonCategory',
    'ReasonSubcategory',
    'ReasonInstance',
    'OEEImpact',
    'ReasonSeverity',
    'get_enabled_categories',
    'is_valid_reason',
    'migrate_from_loss_category',
    'create_reason_instance',
    'taxonomy_manager'
]
