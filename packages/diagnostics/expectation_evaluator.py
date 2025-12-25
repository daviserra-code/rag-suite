"""
Expectation Evaluator
Sprint 4 Extension: Profile Expectations & Escalation Layer

Deterministic, rule-based evaluation of runtime conditions against
domain-specific profile expectations.

KEY PRINCIPLES:
- Runs BEFORE LLM invocation
- Profile-driven, not LLM-driven
- Judgment exists even without LLM
- LLM explains, but does not decide
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def evaluate_profile_expectations(
    runtime_snapshot: Dict[str, Any],
    semantic_signals: Optional[Dict],
    profile
) -> 'ExpectationResult':
    """
    Evaluate runtime conditions against profile-specific expectations.
    
    This is DETERMINISTIC and RULE-BASED.
    Returns structured expectation violations BEFORE LLM call.
    
    Args:
        runtime_snapshot: Current OPC snapshot data
        semantic_signals: Semantic signal data for station/line
        profile: DomainProfile with expectations
    
    Returns:
        ExpectationResult with violations, warnings, blocking conditions
    """
    from apps.shopfloor_copilot.domain_profiles import ExpectationResult
    
    if not profile or not hasattr(profile, 'profile_expectations'):
        # No profile or no expectations - return clean result
        return ExpectationResult(
            violated_expectations=[],
            warnings=[],
            blocking_conditions=[],
            requires_human_confirmation=False,
            severity="normal",
            escalation_tone=False
        )
    
    expectations = profile.profile_expectations
    
    violated_expectations = []
    warnings = []
    blocking_conditions = []
    
    # Extract runtime metrics from semantic signals
    metrics = _extract_runtime_metrics(semantic_signals)
    
    logger.info(f"Evaluating expectations for profile: {profile.display_name}")
    logger.info(f"Runtime metrics: zero_output={metrics['has_zero_output']}, "
                f"reduced_speed={metrics['has_reduced_speed']}, "
                f"station_id={metrics.get('station_id')}, "
                f"material_evidence_present={metrics['material_evidence_present']}, "
                f"quality_status={metrics['material_quality_status']}")
    
    # HOTFIX STEP 2: Missing Material Evidence (Profile-Driven)
    # This must be evaluated FIRST as it's a foundational requirement
    
    # Aerospace & Defence: Missing evidence is BLOCKING
    profile_name_lower = profile.display_name.lower()
    is_aerospace = 'aerospace' in profile_name_lower or 'defence' in profile_name_lower or 'defense' in profile_name_lower
    is_pharma = 'pharma' in profile_name_lower or 'process' in profile_name_lower
    is_automotive = 'automotive' in profile_name_lower or 'discrete' in profile_name_lower
    
    if is_aerospace and not metrics['material_evidence_present']:
        # Aerospace: Missing evidence is a critical violation
        violated_expectations.append("critical_station_requires_evidence")
        blocking_conditions.append("missing_material_context")
        warnings.append(f"Station {metrics.get('station_id')} has no material evidence record")
        
        # Additional blocking for serial mode
        if expectations.missing_serial_binding_is_blocking:
            if not metrics['has_serial_binding']:
                blocking_conditions.append("missing_serial_binding")
    
    # Pharma: Missing evidence is BLOCKING (batch context required)
    if is_pharma and not metrics['material_evidence_present']:
        violated_expectations.append("zero_output_requires_batch_context")
        blocking_conditions.append("missing_batch_context")
        warnings.append(f"Station {metrics.get('station_id')} has no batch/lot context")
    
    # HOTFIX STEP 2: Pharma HOLD/QUARANTINE is BLOCKING
    if is_pharma and metrics['material_quality_status'] in ['HOLD', 'QUARANTINE']:
        violated_expectations.append("quality_hold_blocks_production")
        blocking_conditions.append("material_quality_hold")
        warnings.append(f"Material quality status is {metrics['material_quality_status']} - production blocked")
        
        # If HOLD without deviation, that's also a violation
        if not metrics['has_deviation_record']:
            blocking_conditions.append("missing_deviation_record")
            warnings.append("Quality hold requires deviation record")
    
    # Rule 1: Zero Output Evaluation
    if metrics['has_zero_output']:
        duration = metrics.get('zero_output_duration_minutes', 0)
        
        # Aerospace & Defence: requires authorization
        if expectations.zero_output_requires_authorization:
            if duration >= expectations.zero_output_duration_threshold_minutes:
                violated_expectations.append("zero_output_requires_authorization")
                if _is_critical_station(metrics.get('station_id'), expectations):
                    blocking_conditions.append("missing_authorization_for_critical_station")
                else:
                    warnings.append(f"Zero output for {duration} minutes requires authorization")
        
        # Pharma: requires batch context
        elif expectations.zero_output_requires_batch_context:
            if not metrics.get('has_batch_context'):
                violated_expectations.append("zero_output_requires_batch_context")
                blocking_conditions.append("missing_batch_context")
        
        # Automotive: allowed during startup/changeover
        elif expectations.zero_output_allowed_during_startup:
            if metrics.get('operational_mode') not in ['startup', 'changeover', 'rampup']:
                if duration >= expectations.zero_output_duration_threshold_minutes:
                    warnings.append(f"Zero output for {duration} minutes (not in startup mode)")
    
    # Rule 2: Reduced Speed Evaluation
    if metrics['has_reduced_speed']:
        reduction_percent = metrics.get('speed_reduction_percent', 0)
        
        # Aerospace: requires justification
        if expectations.reduced_speed_requires_justification:
            if reduction_percent >= expectations.speed_reduction_threshold_percent:
                violated_expectations.append("reduced_speed_requires_justification")
                if _is_critical_station(metrics.get('station_id'), expectations):
                    warnings.append(f"Critical station running at {100-reduction_percent}% speed - justification required")
        
        # Pharma: requires deviation
        elif expectations.reduced_speed_requires_deviation:
            if reduction_percent >= expectations.speed_reduction_threshold_percent:
                if not metrics.get('has_deviation_record'):
                    violated_expectations.append("reduced_speed_requires_deviation")
                    blocking_conditions.append("missing_deviation_record")
        
        # Automotive: common during rampup
        elif expectations.reduced_speed_common_during_rampup:
            # No violation - expected behavior
            pass
    
    # Rule 3: Critical Station Evaluation
    if expectations.critical_station_requires_evidence:
        if _is_critical_station(metrics.get('station_id'), expectations):
            if metrics['has_zero_output'] or metrics['has_reduced_speed']:
                if not metrics.get('has_work_order') and not metrics.get('has_maintenance_log'):
                    violated_expectations.append("critical_station_requires_evidence")
                    blocking_conditions.append("missing_evidence_for_critical_station")
    
    # Rule 4: Dry Run Declaration (Aerospace)
    if expectations.dry_run_must_be_declared:
        if metrics['has_zero_output'] and not metrics.get('is_declared_dry_run'):
            if expectations.missing_serial_binding_is_blocking:
                if not metrics.get('has_serial_binding'):
                    violated_expectations.append("missing_serial_binding")
                    blocking_conditions.append("missing_serial_binding_is_blocking")
    
    # Rule 5: Environmental Excursions (Pharma)
    if expectations.environmental_excursion_is_blocking:
        if _check_environmental_limits(metrics, expectations.environmental_limits):
            violated_expectations.append("environmental_excursion")
            blocking_conditions.append("environmental_excursion_is_blocking")
    
    # Determine severity and escalation tone
    requires_human_confirmation = len(blocking_conditions) > 0
    
    if blocking_conditions:
        severity = "critical"
        escalation_tone = True
    elif violated_expectations:
        severity = "warning"
        escalation_tone = True
    else:
        severity = "normal"
        escalation_tone = False
    
    logger.info(f"Expectation evaluation complete: "
                f"violations={len(violated_expectations)}, "
                f"blocking={len(blocking_conditions)}, "
                f"severity={severity}")
    
    return ExpectationResult(
        violated_expectations=violated_expectations,
        warnings=warnings,
        blocking_conditions=blocking_conditions,
        requires_human_confirmation=requires_human_confirmation,
        severity=severity,
        escalation_tone=escalation_tone
    )


def _extract_runtime_metrics(semantic_signals: Optional[Dict]) -> Dict[str, Any]:
    """Extract key metrics from semantic signals for expectation evaluation."""
    metrics = {
        'has_zero_output': False,
        'has_reduced_speed': False,
        'zero_output_duration_minutes': 0,
        'speed_reduction_percent': 0,
        'station_id': None,
        'operational_mode': 'normal',
        'has_batch_context': False,
        'has_deviation_record': False,
        'has_work_order': False,
        'has_maintenance_log': False,
        'is_declared_dry_run': False,
        'has_serial_binding': False,
        # Material evidence (STEP 2)
        'material_context': None,
        'material_evidence_present': False,
        'material_quality_status': None
    }
    
    if not semantic_signals:
        return metrics
    
    # Extract material_context if present (STEP 2 - HOTFIX)
    if 'material_context' in semantic_signals:
        mat_ctx = semantic_signals['material_context']
        metrics['material_context'] = mat_ctx
        metrics['material_evidence_present'] = mat_ctx.get('evidence_present', False)
        metrics['material_quality_status'] = mat_ctx.get('quality_status')
        
        # Update flags based on material evidence
        metrics['has_serial_binding'] = mat_ctx.get('active_serial') is not None
        metrics['has_batch_context'] = mat_ctx.get('active_lot') is not None
        metrics['has_work_order'] = mat_ctx.get('work_order') is not None
        metrics['is_declared_dry_run'] = mat_ctx.get('dry_run_authorization', False)
        metrics['has_deviation_record'] = mat_ctx.get('deviation_id') is not None
    
    # Extract from semantic signals
    signals = semantic_signals.get('semantic_signals', [])
    
    for signal in signals:
        semantic_id = signal.get('semantic_id', '')
        value = signal.get('value', 0)
        
        # Station ID
        if 'station' in semantic_id.lower():
            metrics['station_id'] = signal.get('station_id') or semantic_signals.get('station_id')
        
        # Zero output detection
        if 'count' in semantic_id.lower() and 'good' in semantic_id.lower():
            if value == 0:
                metrics['has_zero_output'] = True
        
        # Speed detection
        if 'speed' in semantic_id.lower() or 'cycle' in semantic_id.lower():
            # Compare to expected (simplified - would need baseline)
            metrics['has_reduced_speed'] = True  # Simplified
            metrics['speed_reduction_percent'] = 15  # Placeholder
        
        # Operational mode (if available)
        if 'mode' in semantic_id.lower():
            mode_str = str(value).lower()
            if 'startup' in mode_str or 'ramp' in mode_str:
                metrics['operational_mode'] = 'startup'
            elif 'changeover' in mode_str:
                metrics['operational_mode'] = 'changeover'
    
    return metrics


def _is_critical_station(station_id: Optional[str], expectations) -> bool:
    """Check if station is in the critical stations list."""
    if not station_id or not expectations.critical_stations:
        return False
    return station_id in expectations.critical_stations


def _check_environmental_limits(metrics: Dict, limits: Dict[str, float]) -> bool:
    """Check if environmental parameters exceed limits."""
    # Simplified - would extract from metrics
    return False  # Placeholder


def format_expectation_violations(expectation_result) -> str:
    """Format expectation violations for LLM context."""
    if not expectation_result.violated_expectations:
        return "No expectation violations detected."
    
    lines = ["PROFILE EXPECTATION VIOLATIONS:"]
    
    for violation in expectation_result.violated_expectations:
        lines.append(f"  • {violation.replace('_', ' ').title()}")
    
    if expectation_result.blocking_conditions:
        lines.append("\nBLOCKING CONDITIONS (require immediate attention):")
        for condition in expectation_result.blocking_conditions:
            lines.append(f"  • {condition.replace('_', ' ').title()}")
    
    if expectation_result.warnings:
        lines.append("\nWARNINGS:")
        for warning in expectation_result.warnings:
            lines.append(f"  • {warning}")
    
    if expectation_result.requires_human_confirmation:
        lines.append("\n⚠️  HUMAN CONFIRMATION REQUIRED")
    
    return "\n".join(lines)
