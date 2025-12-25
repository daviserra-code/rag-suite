#!/usr/bin/env pwsh
<#
.SYNOPSIS
    HOTFIX STEP 2 Verification Script
    Tests missing material evidence violations for A&D and Pharma profiles

.DESCRIPTION
    Validates:
    1. Snapshot includes material_context for all stations (even without DB row)
    2. A&D diagnostics produces blocking conditions for missing evidence
    3. Pharma diagnostics produces blocking for HOLD status
    4. Violations are persisted to database

.NOTES
    Run this after implementing HOTFIX STEP 2
#>

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "HOTFIX STEP 2 - Material Evidence Verification" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Configuration
$OPC_STUDIO_URL = "http://localhost:8040"
$SHOPFLOOR_API_URL = "http://localhost:8000"
$POSTGRES_HOST = "localhost"
$POSTGRES_PORT = 5432
$POSTGRES_USER = "postgres"
$POSTGRES_DB = "ragdb"

# Test counter
$testsPassed = 0
$testsFailed = 0

function Test-Result {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Message = ""
    )
    
    if ($Passed) {
        Write-Host "✅ PASS: $TestName" -ForegroundColor Green
        if ($Message) { Write-Host "   $Message" -ForegroundColor Gray }
        $script:testsPassed++
    } else {
        Write-Host "❌ FAIL: $TestName" -ForegroundColor Red
        if ($Message) { Write-Host "   $Message" -ForegroundColor Yellow }
        $script:testsFailed++
    }
}

# ============================================================================
# Test 1: Semantic Snapshot includes material_context for ST18 (no DB row)
# ============================================================================

Write-Host "`n--- Test 1: Snapshot includes material_context for ST18 ---" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$OPC_STUDIO_URL/semantic/snapshot?station=ST18" -Method Get -ErrorAction Stop
    
    # Check if material_context exists
    if ($response.material_context) {
        $matCtx = $response.material_context
        
        # Check evidence_present flag
        if ($matCtx.PSObject.Properties['evidence_present']) {
            $evidencePresent = $matCtx.evidence_present
            
            Test-Result -TestName "ST18 material_context exists" -Passed $true -Message "evidence_present=$evidencePresent"
            
            # Log the context
            Write-Host "   Material Context for ST18:" -ForegroundColor Gray
            Write-Host "   - Mode: $($matCtx.mode)" -ForegroundColor Gray
            Write-Host "   - Active Serial: $($matCtx.active_serial)" -ForegroundColor Gray
            Write-Host "   - Evidence Present: $evidencePresent" -ForegroundColor Gray
        } else {
            Test-Result -TestName "ST18 material_context exists" -Passed $false -Message "evidence_present field missing"
        }
    } else {
        Test-Result -TestName "ST18 material_context exists" -Passed $false -Message "material_context field missing from response"
    }
} catch {
    Test-Result -TestName "ST18 material_context exists" -Passed $false -Message "Error: $_"
}

# ============================================================================
# Test 2: A&D Diagnostics on ST18 produces blocking conditions
# ============================================================================

Write-Host "`n--- Test 2: A&D diagnostics on ST18 (missing evidence) ---" -ForegroundColor Yellow

try {
    $diagnosticsPayload = @{
        scope = "station"
        id = "ST18"
    } | ConvertTo-Json
    
    $diagResponse = Invoke-RestMethod -Uri "$SHOPFLOOR_API_URL/api/diagnostics/explain" `
        -Method Post `
        -ContentType "application/json" `
        -Body $diagnosticsPayload `
        -ErrorAction Stop
    
    if ($diagResponse.metadata) {
        $meta = $diagResponse.metadata
        
        # Check blocking conditions
        $hasBlockingConditions = $meta.blocking_conditions -and $meta.blocking_conditions.Count -gt 0
        Test-Result -TestName "A&D blocking conditions present" -Passed $hasBlockingConditions -Message "Blocking: $($meta.blocking_conditions -join ', ')"
        
        # Check requires confirmation
        $requiresConfirmation = $meta.requires_confirmation -eq $true
        Test-Result -TestName "A&D requires human confirmation" -Passed $requiresConfirmation
        
        # Check severity
        $isCritical = $meta.severity -eq "critical" -or $meta.severity -eq "warning"
        Test-Result -TestName "A&D severity elevated" -Passed $isCritical -Message "Severity: $($meta.severity)"
        
        # Log expectation violations
        if ($meta.expectation_violations) {
            Write-Host "   Expectation Violations:" -ForegroundColor Gray
            foreach ($violation in $meta.expectation_violations) {
                Write-Host "   - $violation" -ForegroundColor Gray
            }
        }
    } else {
        Test-Result -TestName "A&D diagnostics response" -Passed $false -Message "Missing metadata"
    }
} catch {
    Test-Result -TestName "A&D diagnostics on ST18" -Passed $false -Message "Error: $_"
}

# ============================================================================
# Test 3: Pharma Diagnostics on ST25 (assuming HOLD status exists)
# ============================================================================

Write-Host "`n--- Test 3: Pharma diagnostics on ST25 (HOLD status) ---" -ForegroundColor Yellow

try {
    # First, insert a test material record with HOLD status for ST25
    $insertSql = "INSERT INTO material_instances (plant, line, station, mode, active, active_serial, quality_status) VALUES ('PLANT', 'B01', 'ST25', 'lot', true, 'BATCH-HOLD-001', 'HOLD') ON CONFLICT (plant, line, station, mode) WHERE active = true DO UPDATE SET quality_status = 'HOLD', active_serial = 'BATCH-HOLD-001';"
    
    Write-Host "   Setting up test data for ST25..." -ForegroundColor Gray
    
    # Use Docker exec to run SQL
    docker exec shopfloor-postgres psql -U postgres -d ragdb -c $insertSql 2>&1 | Out-Null
    
    Start-Sleep -Seconds 1
    
    # Now run diagnostics
    $diagnosticsPayload = @{
        scope = "station"
        id = "ST25"
    } | ConvertTo-Json
    
    $diagResponse = Invoke-RestMethod -Uri "$SHOPFLOOR_API_URL/api/diagnostics/explain" `
        -Method Post `
        -ContentType "application/json" `
        -Body $diagnosticsPayload `
        -ErrorAction Stop
    
    if ($diagResponse.metadata) {
        $meta = $diagResponse.metadata
        
        # Check for quality_hold blocking condition
        $hasQualityHold = $meta.blocking_conditions -contains "material_quality_hold"
        Test-Result -TestName "Pharma HOLD is blocking" -Passed $hasQualityHold -Message "Blocking: $($meta.blocking_conditions -join ', ')"
        
        # Check requires confirmation
        $requiresConfirmation = $meta.requires_confirmation -eq $true
        Test-Result -TestName "Pharma HOLD requires confirmation" -Passed $requiresConfirmation
        
        # Check severity
        $isCritical = $meta.severity -eq "critical"
        Test-Result -TestName "Pharma HOLD severity critical" -Passed $isCritical -Message "Severity: $($meta.severity)"
    } else {
        Test-Result -TestName "Pharma diagnostics response" -Passed $false -Message "Missing metadata"
    }
} catch {
    Test-Result -TestName "Pharma diagnostics on ST25" -Passed $false -Message "Error: $_"
}

# ============================================================================
# Test 4: Violations table populated
# ============================================================================

Write-Host "`n--- Test 4: Violations persisted to database ---" -ForegroundColor Yellow

try {
    $violationQuery = "SELECT station, profile, severity, requires_human_confirmation, array_length(blocking_conditions, 1) as blocking_count, ts_start, ts_end FROM violations WHERE station IN ('ST18', 'ST25') ORDER BY ts_start DESC LIMIT 10;"
    
    # Use Docker exec to query violations
    $violationResult = docker exec shopfloor-postgres psql -U postgres -d ragdb -t -A -c $violationQuery 2>&1
    
    if ($LASTEXITCODE -eq 0 -and $violationResult) {
        $violationLines = ($violationResult | Where-Object { $_ -match '\|' })
        $violationCount = $violationLines.Count
        
        if ($violationCount -gt 0) {
            Test-Result -TestName "Violations persisted" -Passed $true -Message "Found $violationCount violation(s)"
            
            Write-Host "   Recent Violations:" -ForegroundColor Gray
            docker exec shopfloor-postgres psql -U postgres -d ragdb -c $violationQuery
        } else {
            Test-Result -TestName "Violations persisted" -Passed $false -Message "No violations found in database"
        }
    } else {
        Test-Result -TestName "Violations persisted" -Passed $false -Message "No violations found or error querying"
    }
} catch {
    Test-Result -TestName "Violations persisted" -Passed $false -Message "Error querying database: $_"
}

# ============================================================================
# Summary
# ============================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "VERIFICATION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Passed: $testsPassed" -ForegroundColor Green
Write-Host "❌ Failed: $testsFailed" -ForegroundColor Red

if ($testsFailed -eq 0) {
    Write-Host "`n🎉 HOTFIX STEP 2 COMPLETE - All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n⚠️  Some tests failed - review output above" -ForegroundColor Yellow
    exit 1
}
