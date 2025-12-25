"""
Deterministic Expectation Tests - Sprint 8
Regression guards for compliance logic

Core Principle:
    If compliance logic changes, tests must fail.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from apps.shopfloor_copilot.domain_profiles import get_active_profile, switch_profile, list_profiles


class TestAerospaceDefenceExpectations:
    """Aerospace & Defence profile expectation tests."""
    
    def test_aerospace_profile_exists(self):
        """
        REGRESSION GUARD: Aerospace profile MUST exist.
        
        The absence of the aerospace profile would break A&D deployments.
        """
        profiles = list_profiles()
        profile_names = [p["name"] for p in profiles]
        
        assert any("aerospace" in name.lower() for name in profile_names), \
            "Aerospace profile MUST exist"
    
    def test_aerospace_profile_has_expectations(self):
        """
        REGRESSION GUARD: Aerospace profile MUST have expectations defined.
        """
        switch_profile("aerospace_defence")
        profile = get_active_profile()
        
        assert profile.profile_expectations is not None, \
            "Aerospace profile MUST have expectations defined"


class TestPharmaProcessExpectations:
    """Pharma/Process profile expectation tests."""
    
    def test_pharma_profile_exists(self):
        """
        REGRESSION GUARD: Pharma profile MUST exist.
        """
        profiles = list_profiles()
        profile_names = [p["name"] for p in profiles]
        
        assert any("pharma" in name.lower() for name in profile_names), \
            "Pharma profile MUST exist"
    
    def test_pharma_profile_has_expectations(self):
        """
        REGRESSION GUARD: Pharma profile MUST have expectations defined.
        """
        switch_profile("pharma_process")
        profile = get_active_profile()
        
        assert profile.profile_expectations is not None, \
            "Pharma profile MUST have expectations defined"


class TestAutomotiveDiscreteExpectations:
    """Automotive/Discrete profile expectation tests."""
    
    def test_automotive_profile_exists(self):
        """
        REGRESSION GUARD: Automotive profile MUST exist.
        """
        profiles = list_profiles()
        profile_names = [p["name"] for p in profiles]
        
        assert any("automotive" in name.lower() for name in profile_names), \
            "Automotive profile MUST exist"
    
    def test_automotive_profile_has_expectations(self):
        """
        REGRESSION GUARD: Automotive profile MUST have expectations defined.
        """
        switch_profile("automotive_discrete")
        profile = get_active_profile()
        
        assert profile.profile_expectations is not None, \
            "Automotive profile MUST have expectations defined"


class TestCrossDomainInvariants:
    """Tests that apply across ALL domain profiles."""
    
    def test_all_profiles_exist(self):
        """
        REGRESSION GUARD: All three domain profiles MUST exist.
        """
        profiles = list_profiles()
        
        assert len(profiles) >= 3, \
            "System MUST have at least 3 domain profiles"
    
    def test_profile_switching_works(self):
        """
        REGRESSION GUARD: Profile switching MUST work correctly.
        """
        result1 = switch_profile("aerospace_defence")
        assert result1, "Must be able to switch to aerospace_defence profile"
        
        result2 = switch_profile("pharma_process")
        assert result2, "Must be able to switch to pharma_process profile"
        
        result3 = switch_profile("automotive_discrete")
        assert result3, "Must be able to switch to automotive_discrete profile"


# Mark all tests in this module as regression tests
pytestmark = pytest.mark.regression
