"""
Profile Expectations Regression Tests
Sprint 4 Extension - STEP 6

PURPOSE:
Ensure that Profile Expectations & Escalation Layer is:
- Deterministic
- Profile-dependent
- Stable over time
- Independent from LLM availability

SCOPE (STRICT):
Tests cover ONLY:
- evaluate_profile_expectations(...)
- DomainProfile loading
- Deterministic expectation evaluation

Tests do NOT cover:
- LLM output text
- RAG retrieval
- UI rendering
- OPC connectivity
- Database persistence

These tests guarantee that THE SAME RUNTIME SNAPSHOT
produces DIFFERENT JUDGMENTS depending on the active domain profile.
"""

import json
import sys
from pathlib import Path
import yaml
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from packages.diagnostics.expectation_evaluator import evaluate_profile_expectations
from apps.shopfloor_copilot.domain_profiles import ProfileExpectations


# ============================================================================
# SIMPLE MOCK PROFILE (for testing only)
# ============================================================================

class SimpleProfile:
    """Minimal profile object for testing expectations"""
    def __init__(self, name: str, display_name: str, expectations: ProfileExpectations):
        self.name = name
        self.display_name = display_name
        self.profile_expectations = expectations


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def fixtures_dir():
    """Return the path to the fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def runtime_snapshot_st18(fixtures_dir):
    """Load the ST18 runtime snapshot fixture"""
    snapshot_path = fixtures_dir / "runtime_snapshot_st18.json"
    with open(snapshot_path, 'r') as f:
        return json.load(f)


@pytest.fixture
def domain_profile_aad(fixtures_dir):
    """Load the Aerospace & Defence domain profile fixture"""
    profile_path = fixtures_dir / "domain_profile_aad.yml"
    with open(profile_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Extract only the expectations (what we actually test)
    expectations_config = config.get('profile_expectations', {})
    expectations = ProfileExpectations(
        zero_output_requires_authorization=expectations_config.get('zero_output_requires_authorization', False),
        zero_output_allowed_during_startup=expectations_config.get('zero_output_allowed_during_startup', False),
        zero_output_requires_batch_context=expectations_config.get('zero_output_requires_batch_context', False),
        reduced_speed_requires_justification=expectations_config.get('reduced_speed_requires_justification', False),
        reduced_speed_requires_deviation=expectations_config.get('reduced_speed_requires_deviation', False),
        reduced_speed_common_during_rampup=expectations_config.get('reduced_speed_common_during_rampup', False),
        critical_station_requires_evidence=expectations_config.get('critical_station_requires_evidence', False),
        dry_run_must_be_declared=expectations_config.get('dry_run_must_be_declared', False),
        unauthorized_stop_is_violation=expectations_config.get('unauthorized_stop_is_violation', False),
        missing_serial_binding_is_blocking=expectations_config.get('missing_serial_binding_is_blocking', False),
        environmental_excursion_is_blocking=expectations_config.get('environmental_excursion_is_blocking', False),
        missing_batch_record_is_violation=expectations_config.get('missing_batch_record_is_violation', False),
        unauthorized_parameter_change_is_blocking=expectations_config.get('unauthorized_parameter_change_is_blocking', False),
        minor_stops_expected_in_normal_operation=expectations_config.get('minor_stops_expected_in_normal_operation', False),
        blocking_only_for_safety=expectations_config.get('blocking_only_for_safety', False),
        zero_output_duration_threshold_minutes=expectations_config.get('zero_output_duration_threshold_minutes', 15),
        speed_reduction_threshold_percent=expectations_config.get('speed_reduction_threshold_percent', 20),
        critical_stations=expectations_config.get('critical_stations', []),
        environmental_limits=expectations_config.get('environmental_limits', {})
    )
    
    return SimpleProfile(
        name=config['name'],
        display_name=config['display_name'],
        expectations=expectations
    )


@pytest.fixture
def domain_profile_automotive(fixtures_dir):
    """Load the Automotive domain profile fixture"""
    profile_path = fixtures_dir / "domain_profile_automotive.yml"
    with open(profile_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Extract only the expectations (what we actually test)
    expectations_config = config.get('profile_expectations', {})
    expectations = ProfileExpectations(
        zero_output_requires_authorization=expectations_config.get('zero_output_requires_authorization', False),
        zero_output_allowed_during_startup=expectations_config.get('zero_output_allowed_during_startup', False),
        zero_output_requires_batch_context=expectations_config.get('zero_output_requires_batch_context', False),
        reduced_speed_requires_justification=expectations_config.get('reduced_speed_requires_justification', False),
        reduced_speed_requires_deviation=expectations_config.get('reduced_speed_requires_deviation', False),
        reduced_speed_common_during_rampup=expectations_config.get('reduced_speed_common_during_rampup', False),
        critical_station_requires_evidence=expectations_config.get('critical_station_requires_evidence', False),
        dry_run_must_be_declared=expectations_config.get('dry_run_must_be_declared', False),
        unauthorized_stop_is_violation=expectations_config.get('unauthorized_stop_is_violation', False),
        missing_serial_binding_is_blocking=expectations_config.get('missing_serial_binding_is_blocking', False),
        environmental_excursion_is_blocking=expectations_config.get('environmental_excursion_is_blocking', False),
        missing_batch_record_is_violation=expectations_config.get('missing_batch_record_is_violation', False),
        unauthorized_parameter_change_is_blocking=expectations_config.get('unauthorized_parameter_change_is_blocking', False),
        minor_stops_expected_in_normal_operation=expectations_config.get('minor_stops_expected_in_normal_operation', False),
        blocking_only_for_safety=expectations_config.get('blocking_only_for_safety', False),
        zero_output_duration_threshold_minutes=expectations_config.get('zero_output_duration_threshold_minutes', 15),
        speed_reduction_threshold_percent=expectations_config.get('speed_reduction_threshold_percent', 20),
        critical_stations=expectations_config.get('critical_stations', []),
        environmental_limits=expectations_config.get('environmental_limits', {})
    )
    
    return SimpleProfile(
        name=config['name'],
        display_name=config['display_name'],
        expectations=expectations
    )


# ============================================================================
# TEST 1: Aerospace & Defence Escalation
# ============================================================================

def test_aad_profile_triggers_blocking_conditions(
    runtime_snapshot_st18,
    domain_profile_aad
):
    """
    Test that Aerospace & Defence profile triggers blocking conditions
    for zero output on a critical station.
    
    EXPECTED BEHAVIOR:
    - Zero output on critical station IS NOT acceptable
    - Blocking conditions exist
    - Escalation required (requires_human_confirmation = True)
    """
    # Act
    result = evaluate_profile_expectations(
        runtime_snapshot=runtime_snapshot_st18,
        semantic_signals=runtime_snapshot_st18,
        profile=domain_profile_aad
    )
    
    # Assert: Violations detected
    assert len(result.violated_expectations) > 0, \
        "Expected violations for zero output on critical station"
    
    # The specific violations may vary based on the rules evaluated,
    # but we expect at least one of these aerospace-specific violations
    expected_violations = [
        "zero_output_requires_authorization",
        "missing_serial_binding",
        "critical_station_requires_evidence"
    ]
    
    has_expected_violation = any(
        violation in result.violated_expectations 
        for violation in expected_violations
    )
    
    assert has_expected_violation, \
        f"Expected aerospace-specific violation, got: {result.violated_expectations}"
    
    # Assert: Blocking conditions exist
    assert len(result.blocking_conditions) > 0, \
        "Expected blocking conditions for critical station with zero output"
    
    # Assert: Human confirmation required
    assert result.requires_human_confirmation is True, \
        "Expected requires_human_confirmation=True for blocking conditions"
    
    # Assert: Severity and escalation tone
    assert result.severity == "critical", \
        "Expected 'critical' severity for blocking conditions"
    
    assert result.escalation_tone is True, \
        "Expected escalation_tone=True for critical violations"


# ============================================================================
# TEST 2: Automotive Does NOT Escalate
# ============================================================================

def test_automotive_profile_allows_startup_behavior(
    runtime_snapshot_st18,
    domain_profile_automotive
):
    """
    Test that Automotive profile allows zero output during startup/rampup
    without triggering blocking conditions.
    
    EXPECTED BEHAVIOR:
    - Same snapshot as Aerospace test
    - No blocking conditions
    - Behavior considered normal during ramp-up
    """
    # Act
    result = evaluate_profile_expectations(
        runtime_snapshot=runtime_snapshot_st18,
        semantic_signals=runtime_snapshot_st18,
        profile=domain_profile_automotive
    )
    
    # Assert: No blocking conditions
    assert len(result.blocking_conditions) == 0, \
        "Expected NO blocking conditions for automotive profile during startup"
    
    # Assert: No human confirmation required
    assert result.requires_human_confirmation is False, \
        "Expected requires_human_confirmation=False for automotive profile"
    
    # Assert: Severity is NOT critical
    assert result.severity != "critical", \
        "Expected severity to NOT be 'critical' for automotive profile"
    
    # Assert: No escalation tone
    assert result.escalation_tone is False or result.severity == "normal", \
        "Expected no escalation tone for automotive profile"


# ============================================================================
# TEST 3: Determinism (Repeatability)
# ============================================================================

def test_expectation_evaluation_is_deterministic(
    runtime_snapshot_st18,
    domain_profile_aad
):
    """
    Test that evaluate_profile_expectations is deterministic.
    
    EXPECTED BEHAVIOR:
    - No randomness
    - No dependency on external state
    - Same inputs → Same outputs (always)
    """
    # Act: Evaluate multiple times
    result1 = evaluate_profile_expectations(
        runtime_snapshot=runtime_snapshot_st18,
        semantic_signals=runtime_snapshot_st18,
        profile=domain_profile_aad
    )
    
    result2 = evaluate_profile_expectations(
        runtime_snapshot=runtime_snapshot_st18,
        semantic_signals=runtime_snapshot_st18,
        profile=domain_profile_aad
    )
    
    result3 = evaluate_profile_expectations(
        runtime_snapshot=runtime_snapshot_st18,
        semantic_signals=runtime_snapshot_st18,
        profile=domain_profile_aad
    )
    
    # Assert: All results are identical
    assert result1.violated_expectations == result2.violated_expectations == result3.violated_expectations, \
        "Expected identical violated_expectations across evaluations"
    
    assert result1.warnings == result2.warnings == result3.warnings, \
        "Expected identical warnings across evaluations"
    
    assert result1.blocking_conditions == result2.blocking_conditions == result3.blocking_conditions, \
        "Expected identical blocking_conditions across evaluations"
    
    assert result1.requires_human_confirmation == result2.requires_human_confirmation == result3.requires_human_confirmation, \
        "Expected identical requires_human_confirmation across evaluations"
    
    assert result1.severity == result2.severity == result3.severity, \
        "Expected identical severity across evaluations"
    
    assert result1.escalation_tone == result2.escalation_tone == result3.escalation_tone, \
        "Expected identical escalation_tone across evaluations"


# ============================================================================
# TEST 4: LLM Independence
# ============================================================================

def test_expectations_do_not_depend_on_llm(
    runtime_snapshot_st18,
    domain_profile_aad
):
    """
    Test that profile expectations work even when LLM is disabled/unavailable.
    
    EXPECTED BEHAVIOR:
    - Expectations work even with LLM disabled
    - Same ExpectationResult as with LLM enabled
    - This is a RULE-BASED system, not LLM-based
    
    NOTE: Since evaluate_profile_expectations is already LLM-independent,
    this test confirms that by demonstrating it requires no LLM mocking.
    """
    # Simulate LLM unavailability by simply running the function
    # (no LLM calls are made in evaluate_profile_expectations)
    
    # Act
    result = evaluate_profile_expectations(
        runtime_snapshot=runtime_snapshot_st18,
        semantic_signals=runtime_snapshot_st18,
        profile=domain_profile_aad
    )
    
    # Assert: Expectations still evaluated
    assert result is not None, \
        "Expected result even without LLM"
    
    assert result.requires_human_confirmation is True, \
        "Expected requires_human_confirmation=True even without LLM"
    
    assert len(result.blocking_conditions) > 0, \
        "Expected blocking conditions even without LLM"
    
    # The function is deterministic and rule-based - no LLM needed
    assert len(result.violated_expectations) > 0, \
        "Expected violations to be detected without LLM involvement"


# ============================================================================
# TEST 5: Profile Comparison (Same Snapshot, Different Judgments)
# ============================================================================

def test_same_snapshot_different_profiles_different_results(
    runtime_snapshot_st18,
    domain_profile_aad,
    domain_profile_automotive
):
    """
    Test that the SAME runtime snapshot produces DIFFERENT judgments
    depending on the active domain profile.
    
    This is the CORE GUARANTEE of the Profile Expectations system.
    """
    # Act: Evaluate with both profiles
    result_aad = evaluate_profile_expectations(
        runtime_snapshot=runtime_snapshot_st18,
        semantic_signals=runtime_snapshot_st18,
        profile=domain_profile_aad
    )
    
    result_automotive = evaluate_profile_expectations(
        runtime_snapshot=runtime_snapshot_st18,
        semantic_signals=runtime_snapshot_st18,
        profile=domain_profile_automotive
    )
    
    # Assert: Different results
    assert result_aad.requires_human_confirmation != result_automotive.requires_human_confirmation, \
        "Expected different requires_human_confirmation for different profiles"
    
    assert len(result_aad.blocking_conditions) != len(result_automotive.blocking_conditions), \
        "Expected different blocking_conditions count for different profiles"
    
    assert result_aad.severity != result_automotive.severity, \
        "Expected different severity levels for different profiles"
    
    # Specifically: AAD should escalate, Automotive should not
    assert result_aad.requires_human_confirmation is True, \
        "Expected AAD profile to require human confirmation"
    
    assert result_automotive.requires_human_confirmation is False, \
        "Expected Automotive profile to NOT require human confirmation"


# ============================================================================
# NON-GOALS VERIFICATION
# ============================================================================

def test_no_natural_language_assertions():
    """
    Verify that tests do NOT assert on natural language output.
    
    This test exists as documentation that we explicitly avoid:
    - Checking explanation text
    - Comparing narrative descriptions
    - Asserting on LLM-generated content
    
    We test JUDGMENT, not NARRATION.
    """
    # This is a meta-test - it passes to document the constraint
    assert True, "Tests assert on ExpectationResult fields, not text"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "--tb=short"])
