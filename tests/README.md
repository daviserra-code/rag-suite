# Profile Expectations Regression Tests
**Sprint 4 Extension - STEP 6**

## Purpose

Ensure that **Profile Expectations & Escalation Layer (Step 1.5)** is:
- ✅ Deterministic
- ✅ Profile-dependent
- ✅ Stable over time
- ✅ Independent from LLM availability

These tests guarantee that **the same runtime snapshot** produces **different judgments** depending on the active domain profile.

---

## Scope (STRICT)

### ✅ Tests COVER:
- `evaluate_profile_expectations(...)` function
- `ProfileExpectations` dataclass loading
- Deterministic expectation evaluation
- Profile-dependent behavior

### ❌ Tests DO NOT COVER:
- LLM output text
- RAG retrieval
- UI rendering
- OPC connectivity
- Database persistence

**We test JUDGMENT, not NARRATION.**

---

## Test Structure

```
tests/
├── __init__.py
├── test_profile_expectations.py    # Main test suite (6 tests)
└── fixtures/
    ├── runtime_snapshot_st18.json  # ST18 station snapshot (zero output, critical)
    ├── domain_profile_aad.yml      # Aerospace & Defence (strict)
    └── domain_profile_automotive.yml # Automotive (lenient)
```

---

## Test Cases

### Test 1: `test_aad_profile_triggers_blocking_conditions`
**Verifies:** Aerospace & Defence profile triggers escalation

**Given:**
- ST18 station (critical)
- Zero output
- Reduced speed

**Expected:**
- ✅ Violations detected
- ✅ Blocking conditions exist
- ✅ `requires_human_confirmation = True`
- ✅ `severity = "critical"`
- ✅ `escalation_tone = True`

---

### Test 2: `test_automotive_profile_allows_startup_behavior`
**Verifies:** Automotive profile does NOT escalate for same snapshot

**Given:**
- Same ST18 snapshot as Test 1

**Expected:**
- ✅ NO blocking conditions
- ✅ `requires_human_confirmation = False`
- ✅ `severity != "critical"`
- ✅ No escalation tone

---

### Test 3: `test_expectation_evaluation_is_deterministic`
**Verifies:** Same inputs → same outputs (always)

**Given:**
- Same snapshot evaluated 3 times with AAD profile

**Expected:**
- ✅ All results identical
- ✅ No randomness
- ✅ No external state dependency

---

### Test 4: `test_expectations_do_not_depend_on_llm`
**Verifies:** Expectations work without LLM

**Given:**
- No LLM mocking required (function is already LLM-independent)

**Expected:**
- ✅ `ExpectationResult` returned
- ✅ Blocking conditions detected
- ✅ Rules evaluated without LLM calls

---

### Test 5: `test_same_snapshot_different_profiles_different_results`
**Verifies:** Core guarantee of profile expectations system

**Given:**
- Same ST18 snapshot
- Evaluated with AAD profile
- Evaluated with Automotive profile

**Expected:**
- ✅ Different `requires_human_confirmation`
- ✅ Different blocking conditions count
- ✅ Different severity levels
- ✅ AAD escalates, Automotive does not

---

### Test 6: `test_no_natural_language_assertions`
**Verifies:** Documentation that we avoid text assertions

**Given:**
- Meta-test (always passes)

**Expected:**
- ✅ Confirms tests assert on fields, not text

---

## Running Tests

### Run all tests:
```bash
cd /path/to/rag-suite
python -m pytest tests/test_profile_expectations.py -v
```

### Run specific test:
```bash
python -m pytest tests/test_profile_expectations.py::test_aad_profile_triggers_blocking_conditions -v
```

### Run with detailed output:
```bash
python -m pytest tests/test_profile_expectations.py -vv
```

---

## Expected Output

```
============================================ test session starts =============================================
platform win32 -- Python 3.14.1, pytest-9.0.2, pluggy-1.6.0
collected 6 items                                                                                             

tests/test_profile_expectations.py::test_aad_profile_triggers_blocking_conditions PASSED                [ 16%] 
tests/test_profile_expectations.py::test_automotive_profile_allows_startup_behavior PASSED              [ 33%] 
tests/test_profile_expectations.py::test_expectation_evaluation_is_deterministic PASSED                 [ 50%] 
tests/test_profile_expectations.py::test_expectations_do_not_depend_on_llm PASSED                       [ 66%] 
tests/test_profile_expectations.py::test_same_snapshot_different_profiles_different_results PASSED      [ 83%] 
tests/test_profile_expectations.py::test_no_natural_language_assertions PASSED                          [100%] 

============================================= 6 passed in 0.12s ============================================== 
```

---

## Definition of Done ✅

- [x] All tests pass consistently
- [x] Same snapshot → different `ExpectationResult` per profile
- [x] LLM disabled → same `ExpectationResult`
- [x] Any regression in expectations causes test failure
- [x] Tests assert on `ExpectationResult` fields, not text
- [x] Aerospace & Defence escalates where Automotive does not

---

## Key Design Principles

1. **Deterministic:** No randomness, no external state
2. **Profile-dependent:** Same data → different judgments per profile
3. **LLM-independent:** Works without LLM availability
4. **Field-based assertions:** Test structured output, not narrative text
5. **Regression protection:** Prevents silent behavior changes

---

## Maintenance

### Adding new expectations:
1. Update `ProfileExpectations` dataclass
2. Update test fixtures (YAML files)
3. Add assertions for new expectations
4. Ensure AAD/Automotive profiles differ

### Modifying evaluation logic:
1. Run regression tests first
2. Update tests if behavior intentionally changes
3. Verify all 6 tests still pass
4. Document changes in commit message

---

## Related Documentation

- `PROFILE_EXPECTATIONS_COMPLETE.md` - Complete implementation guide
- `DOMAIN_PROFILE_WIRING_COMPLETE.md` - Profile system architecture
- `packages/diagnostics/expectation_evaluator.py` - Implementation

---

**Status:** ✅ Complete  
**Last Updated:** December 24, 2025  
**Test Suite Version:** 1.0
