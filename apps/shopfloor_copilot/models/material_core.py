"""
Material Intelligence Core
Sprint 4 — Material Intelligence & Domain Profiles

UNIFIED material model valid for all domains:
- Aerospace & Defence (serial-level traceability)
- Pharma / Process (batch/lot traceability)
- Automotive / Discrete (lot-level traceability)

Domain profiles define:
- Whether instance_id is serial or lot
- Which fields are mandatory
- Validation strictness

DESIGN PRINCIPLES:
- Single material model, no domain-specific variants
- Profile-driven behavior, not hardcoded logic
- Read-only data model (observability, not control)
- Immutable genealogy links
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class MaterialState(str, Enum):
    """Material state in the manufacturing process"""
    AVAILABLE = "available"              # Ready for use
    IN_PROCESS = "in_process"            # Currently being processed
    CONSUMED = "consumed"                # Fully consumed
    QUARANTINE = "quarantine"            # Quality hold
    EXPIRED = "expired"                  # Past expiry date
    SCRAPPED = "scrapped"                # Rejected/scrapped
    SHIPPED = "shipped"                  # Shipped to customer
    RETURNED = "returned"                # Returned from customer


class QualityStatus(str, Enum):
    """Quality inspection status"""
    NOT_INSPECTED = "not_inspected"      # Awaiting inspection
    PASSED = "passed"                    # Inspection passed
    FAILED = "failed"                    # Inspection failed
    CONDITIONAL = "conditional"          # Passed with conditions
    AWAITING_APPROVAL = "awaiting_approval"  # Pending approval
    APPROVED = "approved"                # Fully approved
    REJECTED = "rejected"                # Rejected


@dataclass
class MaterialDefinition:
    """
    Material definition (master data).
    
    Represents the "what" - the part specification independent of instances.
    Valid for all domains.
    """
    part_number: str                     # Unique part identifier
    revision: str                        # Revision/version
    description: Optional[str] = None
    specification: Optional[str] = None  # Spec reference
    uom: str = "EA"                      # Unit of measure
    
    # Domain-dependent (validated by profile)
    supplier: Optional[str] = None
    supplier_part_number: Optional[str] = None
    
    # Aerospace/Pharma specific (optional in other domains)
    certificate_reference: Optional[str] = None
    regulatory_classification: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate based on active domain profile"""
        from ..domain_profiles import profile_manager
        
        profile = profile_manager.get_active_profile()
        
        # Check mandatory fields based on profile
        for field_name in profile.material_model.material_mandatory_fields:
            value = getattr(self, field_name, None)
            if value is None or value == '':
                raise ValueError(
                    f"Field '{field_name}' is mandatory for "
                    f"{profile.display_name} profile"
                )


@dataclass
class MaterialInstance:
    """
    Material instance (lot OR serial).
    
    Represents a specific quantity of material with traceability.
    Profile determines whether instance_id is serial or lot.
    """
    instance_id: str                     # Serial number OR lot number (profile-dependent)
    material_definition: MaterialDefinition
    quantity: float                      # Quantity (1.0 for serialized parts)
    state: MaterialState = MaterialState.AVAILABLE
    
    # Location & ownership
    location: Optional[str] = None       # Warehouse, station, etc.
    work_order: Optional[str] = None     # Associated work order
    operation_id: Optional[str] = None   # Current operation
    
    # Quality & compliance
    quality_status: QualityStatus = QualityStatus.NOT_INSPECTED
    quality_notes: Optional[str] = None
    
    # Traceability (Aerospace/Pharma critical)
    batch_number: Optional[str] = None   # Pharma batch tracking
    lot_number: Optional[str] = None     # Lot tracking
    serial_number: Optional[str] = None  # Serial tracking
    
    # Dates
    manufactured_date: Optional[datetime] = None
    received_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    
    # Certifications (Aerospace/Pharma)
    certificate_of_analysis: Optional[str] = None  # COA reference
    certificate_of_conformance: Optional[str] = None  # COC reference
    test_report_reference: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_serialized(self) -> bool:
        """Check if this is a serialized (unique) instance"""
        from ..domain_profiles import profile_manager
        profile = profile_manager.get_active_profile()
        return profile.material_model.identification == 'serial'
    
    @property
    def is_expired(self) -> bool:
        """Check if material is expired (if expiry management applies)"""
        from ..domain_profiles import profile_manager
        profile = profile_manager.get_active_profile()
        
        if profile.material_model.expiry_management == 'none':
            return False
        
        if self.expiry_date is None:
            if profile.material_model.expiry_management == 'mandatory':
                raise ValueError("Expiry date is mandatory but not set")
            return False
        
        return datetime.utcnow() > self.expiry_date
    
    @property
    def requires_certification(self) -> bool:
        """Check if certification is required for this material"""
        from ..domain_profiles import profile_manager
        profile = profile_manager.get_active_profile()
        
        # Aerospace always requires certification
        if profile.name == 'aerospace_defence':
            return True
        
        # Pharma requires COA
        if profile.name == 'pharma_process':
            return True
        
        return False
    
    def validate_for_use(self) -> tuple[bool, List[str]]:
        """
        Validate if material instance can be used.
        
        Returns:
            (is_valid, list_of_issues)
        """
        from ..domain_profiles import profile_manager
        profile = profile_manager.get_active_profile()
        
        issues = []
        
        # State check
        if self.state not in [MaterialState.AVAILABLE, MaterialState.IN_PROCESS]:
            issues.append(f"Material state is {self.state.value}, not available for use")
        
        # Expiry check
        if self.is_expired:
            issues.append(f"Material expired on {self.expiry_date}")
        
        # Quality check
        if profile.process_constraints.quality_gate_enforcement == 'strict':
            if self.quality_status not in [QualityStatus.PASSED, QualityStatus.APPROVED]:
                issues.append(f"Quality status is {self.quality_status.value}, requires approval")
        
        # Certification check (Aerospace/Pharma)
        if self.requires_certification:
            if profile.name == 'aerospace_defence':
                if not self.certificate_of_conformance:
                    issues.append("Certificate of Conformance missing (A&D requirement)")
            elif profile.name == 'pharma_process':
                if not self.certificate_of_analysis:
                    issues.append("Certificate of Analysis missing (Pharma requirement)")
        
        return len(issues) == 0, issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'instance_id': self.instance_id,
            'part_number': self.material_definition.part_number,
            'revision': self.material_definition.revision,
            'description': self.material_definition.description,
            'quantity': self.quantity,
            'state': self.state.value,
            'location': self.location,
            'work_order': self.work_order,
            'quality_status': self.quality_status.value,
            'batch_number': self.batch_number,
            'lot_number': self.lot_number,
            'serial_number': self.serial_number,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'is_expired': self.is_expired,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class GenealogyLink:
    """
    Immutable genealogy link between material instances.
    
    Records parent-child relationships during manufacturing operations.
    Critical for Aerospace & Pharma traceability.
    """
    link_id: str                         # Unique link identifier
    parent_instance: MaterialInstance    # Input material
    child_instance: MaterialInstance     # Output material
    operation_id: str                    # Operation that created the link
    work_order: Optional[str] = None     # Associated work order
    
    # Context
    consumed_quantity: float = 0.0       # How much of parent was consumed
    produced_quantity: float = 0.0       # How much of child was produced
    
    # Traceability
    operator: Optional[str] = None
    station_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Documentation (Aerospace critical)
    work_instruction_reference: Optional[str] = None
    deviation_reference: Optional[str] = None
    
    # Metadata (immutable record)
    recorded_at: datetime = field(default_factory=datetime.utcnow)
    recorded_by: Optional[str] = None    # System or user who created link
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'link_id': self.link_id,
            'parent_instance_id': self.parent_instance.instance_id,
            'child_instance_id': self.child_instance.instance_id,
            'operation_id': self.operation_id,
            'work_order': self.work_order,
            'consumed_quantity': self.consumed_quantity,
            'produced_quantity': self.produced_quantity,
            'operator': self.operator,
            'station_id': self.station_id,
            'timestamp': self.timestamp.isoformat(),
            'work_instruction_reference': self.work_instruction_reference,
            'deviation_reference': self.deviation_reference,
            'recorded_at': self.recorded_at.isoformat(),
            'recorded_by': self.recorded_by
        }


@dataclass
class MaterialGenealogyTree:
    """
    Material genealogy tree (forward or backward tracing).
    
    Supports:
    - Forward tracing: raw material → finished goods
    - Backward tracing: finished goods → raw materials
    """
    root_instance: MaterialInstance
    depth: str  # 'shallow' or 'deep' (from profile)
    links: List[GenealogyLink] = field(default_factory=list)
    
    def add_link(self, link: GenealogyLink):
        """Add a genealogy link to the tree"""
        self.links.append(link)
    
    def get_parents(self, instance: MaterialInstance) -> List[MaterialInstance]:
        """Get all parent materials for an instance"""
        return [
            link.parent_instance 
            for link in self.links 
            if link.child_instance.instance_id == instance.instance_id
        ]
    
    def get_children(self, instance: MaterialInstance) -> List[MaterialInstance]:
        """Get all child materials for an instance"""
        return [
            link.child_instance 
            for link in self.links 
            if link.parent_instance.instance_id == instance.instance_id
        ]
    
    def trace_backward(self, max_depth: int = 10) -> List[MaterialInstance]:
        """
        Trace backward from root to all source materials.
        
        Returns list of all parent materials up to max_depth.
        """
        visited = set()
        result = []
        
        def recurse(instance: MaterialInstance, current_depth: int):
            if current_depth > max_depth:
                return
            
            if instance.instance_id in visited:
                return
            
            visited.add(instance.instance_id)
            parents = self.get_parents(instance)
            
            for parent in parents:
                result.append(parent)
                recurse(parent, current_depth + 1)
        
        recurse(self.root_instance, 0)
        return result
    
    def trace_forward(self, max_depth: int = 10) -> List[MaterialInstance]:
        """
        Trace forward from root to all derived materials.
        
        Returns list of all child materials up to max_depth.
        """
        visited = set()
        result = []
        
        def recurse(instance: MaterialInstance, current_depth: int):
            if current_depth > max_depth:
                return
            
            if instance.instance_id in visited:
                return
            
            visited.add(instance.instance_id)
            children = self.get_children(instance)
            
            for child in children:
                result.append(child)
                recurse(child, current_depth + 1)
        
        recurse(self.root_instance, 0)
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert genealogy tree to dictionary"""
        return {
            'root_instance': self.root_instance.to_dict(),
            'depth': self.depth,
            'total_links': len(self.links),
            'links': [link.to_dict() for link in self.links]
        }


# Utility functions for material management

def create_material_instance(
    part_number: str,
    revision: str,
    instance_id: str,
    quantity: float,
    **kwargs
) -> MaterialInstance:
    """
    Factory function to create a material instance.
    
    Automatically validates against active domain profile.
    """
    from ..domain_profiles import profile_manager
    
    profile = profile_manager.get_active_profile()
    
    # Create material definition
    mat_def = MaterialDefinition(
        part_number=part_number,
        revision=revision,
        description=kwargs.get('description'),
        specification=kwargs.get('specification'),
        supplier=kwargs.get('supplier'),
        certificate_reference=kwargs.get('certificate_reference')
    )
    
    # Create instance
    instance = MaterialInstance(
        instance_id=instance_id,
        material_definition=mat_def,
        quantity=quantity,
        state=kwargs.get('state', MaterialState.AVAILABLE),
        location=kwargs.get('location'),
        quality_status=kwargs.get('quality_status', QualityStatus.NOT_INSPECTED),
        batch_number=kwargs.get('batch_number'),
        lot_number=kwargs.get('lot_number'),
        serial_number=kwargs.get('serial_number'),
        expiry_date=kwargs.get('expiry_date'),
        certificate_of_analysis=kwargs.get('certificate_of_analysis'),
        certificate_of_conformance=kwargs.get('certificate_of_conformance')
    )
    
    return instance


def validate_material_for_profile(instance: MaterialInstance) -> tuple[bool, List[str]]:
    """
    Validate material instance against active profile requirements.
    
    Returns:
        (is_valid, list_of_validation_errors)
    """
    return instance.validate_for_use()
